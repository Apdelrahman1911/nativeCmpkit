# One failed Dont-keep method — source-only recovery candidate

[Native009](../restoration-ci009/README.md) remains FAILED: actual API35 **3/4
methods pass**, one XML, Gradle1/77.02s. Dont-keep stops at original
`AndroidCameraRestorationTest.kt:156`, waiting for `destroys>0`. Scalar1 was
observed; cached AMS state was not. The destruction timeout's cause remains
**unknown**. Twenty-four cumulative restoration executions contain three accepted
outcomes; those three methods are reused, not replayed. **#13 stays open.**

## Frozen candidate and protected scope

- Base: `5585edacd97dfb0eb928507a9e9017630dfc7c14`.
- Seven files: five owning existing files and two new test-only files.
- Patch SHA256:
  `9d1c53cbf3d28310014cccf984b3bf794b55aaf6e3c1686e2ce3cdcb07240a5a`.
- Selected **1,012 library / 1,089 combined source inputs**; strict zero-fuzz patch
  dry-run passes. No compilation, new native execution or verification dispatch
  is represented by this candidate evidence.

The finite `android-camera-restoration-dont-keep` profile selects only
`AndroidCameraRestorationTest#nativeDontKeepActivitiesRestoresOneReadableCapturedFile`
on owned API35. The original four-method profile remains available.

Workflow/matrix changes add only that camera choice/profile. Library-tooling
changes are camera-specific selection, identities, validation and fresh-XML
branches. Inverting the camera hunks reproduces the entire frozen CI preimages:
all I/O/helper/source-contract hooks, browser behavior, **11 full slots** and
**eight Android modules** remain exact.

Reporter changes own only Dont-keep arming/restoration and its shell-reader bound:
65,536 bytes remains the default; 1 MiB is permitted only for exact
`dumpsys activity processes`. The original destruction/public-launcher/native
registry/grant/readable-file assertions are unchanged. Accepted false-branch
source is equivalent; receiver/client/production/manifest/dependencies are unchanged.
Only the directly affected existing reader guard is repaired, with three stronger
confinement assertions. New files are `OwnedAlwaysFinish.kt` and its twenty guards.

## Source-backed contract, not an actual failure diagnosis

Pinned Android15 Settings uses genuine `IActivityManager.setAlwaysFinish(boolean)`;
AMS writes the scalar and its cached boolean. The candidate derives the transaction
from the running generated Stub, checks signature/name/descriptor and actual Shell
UID2000/user0/permission, and requires the exact successful Parcel reply. No guessed
transaction, hidden-API policy change, permission adoption or fallback is authorized.

Native state is read in memory only from a complete, bounded, unique AMS processes
schema. False-by-omission is permitted only inside that pinned complete-query
schema. Ownership precedes uncertain IPCs; inconsistent originals and foreign or
unknown state refuse. Restoration uses the native setter and deletes only a
verified setter-created zero row when restoring original scalar absence. Primary
and cleanup failures are preserved. No forced destruction, manual grants or
registry/result substitution is introduced.

Actual reflective access, generated transaction access, native dump shape and
Parcel reply remain **unexecuted**. The source distinction does not establish the
timeout cause or guarantee Activity destruction. Every refusal remains a failure.

## Recorded checks and evidence

- `important-method-results.json`: two initial new owning reds (one error, one
  failure), twenty new source/model passes, and one existing reader guard's
  red/repair/fresh pass: **21 distinct important methods**, not native outcomes.
  The accepted twenty methods were not replayed after exact source-correspondence
  review. Original private log digests are retained without private paths or
  whole-source assertion payloads.
- `source-correspondence.json` and `candidate-identities.json`: protected equality,
  immutable per-file pre/post hashes, Git preimages and private inventory digests.
- `android15-source-references.json`: pinned public URLs/line ranges/source hashes;
  failed preliminary404 lookups remain recorded. Original source bytes remain private.
- `plan-and-lint-readbacks.json`: pure plans for one-method/four-method camera,
  I/O provider and JS/Wasm browser profiles; API23 refuses, exit2. Existing pinned
  Actionlint1.7.12 passes with explicit `-shellcheck= -pyflakes=` omissions.
- `rebase-context-refusals.json`: two strict changed-I/O-context refusals preserved;
  only the camera choice and camera validation contexts were manually resolved.

Next: lead-owned reporter compilation when capacity permits, then only the failed
Dont-keep native method and independent source/results/ownership review. No closure,
publication/Pages/main/history, minimum/physical/consumer/ABI/dependency/legal/
security/readiness or capacity gate changes.
