# macOS preparation postcondition diagnostics — D1 R2, 2026-11-06

## Verified scope

Base: `development/macos-parent-lease-20261105` at `f69800f86080339f690b909032567e7077f52d32`.
This is **source-only** preparation failure diagnosis; it does not repair native
parenting or establish compiler, JNI/AWT, consumer, or issue #58 acceptance.

- Three existing sources / five exact reversible spans, plus one new test source,
  adopted once. Existing inodes, modes, ownership and atimes preserved; NEW0644.
- **NEW8: 8/8 once**; genuine `Ran 8 tests in 0.071s` / `OK`.
  Child0 / 0.449606s / complete1862B EOF; source receipt0.689785s.
  Lead outer0.768447s is a separate observation, not the suite or child time.
- Original1546 source baseline; post-adoption1547 maps identical before/after.
  All1543 untouched source full10 identities held; owned HOME/tmp removed;
  process group absent. Q300/source270/cleanup30 unchanged.
- Existing preparation predicate, native commands, task membership, privacy caps,
  minimum contents:read permissions and five-JSON hosted allowlist unchanged.
  The new optional receipt only exposes bounded fixed-schema operand observations
  after the original predicate has already refused; classifier errors cannot mask it.

## Sparse-checkout recovery, without history/index changes

A passive named-prefix observation found `build.gradle.kts` currently unavailable.
It does **not** prove the historical D1 exception's missing operand or cause.
The lead materialized exactly997 missing declared f698 Git blobs and1454 ancestor
directories in one batch. Existing549 source identities were retained. No existing
file was overwritten; all restored blob SHA256/Git object IDs and tracked modes held.

The original materializer is preserved as **REFUSED_PARTIAL_PRESERVED** after all997
writes: its local final directory-map condition omitted the root entry. It was
not rerun and no writes were reapplied. A separate **zero-write passive readback**
qualified all1546 sources /1480 directories /16748920B and held both existing549 and
created997 full10 identities. This is namespace/source custody, not native evidence.

## Original failures and next action

Original run [42153089976](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/42153089976),
attempt1, stays FAILED: Gradle PREPARE child0/278.224342s/complete18710B, then a
postcondition refusal with no established rejecting operand. Zero native/JUnit.
Original local D1 stays FAILED before adoption/tests; original marker/evidence
untouched. Fresh D1 R2 changed only routing pins before the one successful NEW8 run.

Next: one changed **PREPARE-only** request at the newly committed branch HEAD,
with fresh max-two combined hosted capacity including queued/reserved runs.
Do not retry the unchanged failed f698 request. Genuine native parenting and
all release/security/consumer/API–ABI gates remain; #58 stays open.
No package, release or deployment publication.

## Preserved evidence

`source-evidence.zip` contains exact original JSON/log payloads, the reviewed
plan, independent saved-results review, adoption journal, and sparse recovery
original/passive receipts. Compression keeps large custody maps out of repeated
source/fixture text copies; nothing is substituted for executable library tests.

Archive: 667026B, SHA256 `cb0a3cb2982628743e87ca9f48e8bba2c5e9f94e215d84d7e514d7b0137232cd`.
Read without extracting source paths: `python3 -m zipfile -l source-evidence.zip`.
All identities inside JSON are native Python integer nanoseconds (never JS-rounded).
The protected Windows success trace was never read, statted, scanned or staged.

| Entry | Bytes | SHA256 |
|---|---:|---|
| `SOURCE-RESULT.json` | 4106 | `fbf93e7bf592767172471a2d6d3f2f44509c8d8fef4c40920059013426da2c8f` |
| `NEW8-ORIGINAL.log` | 1862 | `2f6c72b410069612a524ad7376dadd181739553a98e496123017d8257180ad48` |
| `SOURCE-RESULTS-REVIEW.json` | 16259 | `a0c5657ad71562dd27af0a3022751775683604fd71f9556e732b4e7a8557213c` |
| `OWNING-PLAN.json` | 18417 | `a35b224cb5996437cf927064140609a67201b3271940e73857264554489b0c5f` |
| `ORIGINAL-SAFE-SOURCES.json` | 415291 | `667559221524321a36b23d596fb5655f6197c1b38e1b85c839496cea6356a0f3` |
| `SAFE-SOURCES-BEFORE.json` | 415533 | `65a66fd5ea3fc7cf25b53af5bcccaf5f659d780e805c907220c5e83a4ee5c7cb` |
| `SAFE-SOURCES-AFTER.json` | 415533 | `65a66fd5ea3fc7cf25b53af5bcccaf5f659d780e805c907220c5e83a4ee5c7cb` |
| `ADOPTION-JOURNAL.jsonl` | 861 | `0207b26c5bd55a28504eb910ee37f3da39f9ff4a350d1583220cdce3ac86fedf` |
| `SPARSE-MATERIALIZATION-ORIGINAL.json` | 1348793 | `d04b7a3d50fcfaca9f9cf857f013210938a07972eef4c62e34be88da7d504480` |
| `SPARSE-PASSIVE-RESULT.json` | 1048867 | `6dcd8d8405caf04c9e3f66f5962943eba0caae82a041c740d51c587775ac52c1` |
| `ARCHIVED-REFS.json` | 5662 | `a364747c4176240043be8a2419a9b9a2166ad990ae1a6b88d67f29a6c44ad490` |
