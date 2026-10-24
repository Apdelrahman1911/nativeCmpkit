# [High][IO-002] Android saver loses pending content across recomposition and can report an empty export as success

<!-- nativecmpkit-item:audit:IO-002 -->
## Classification
- **Finding:** IO-002
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/picker/FileSaverLauncher.android.kt:31-32`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/picker/FileSaverLauncher.android.kt#L31-L32) — `pendingSource`
- [`calf-file-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/picker/FileSaverLauncher.android.kt:34-60`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/picker/FileSaverLauncher.android.kt#L34-L60) — `ActivityResult callback`
- [`calf-file-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/picker/FileSaverLauncher.android.kt:65-74`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/picker/FileSaverLauncher.android.kt#L65-L74) — `remembered launch lambdas`

## Root cause
remember<Any?> { null } remembers null, not a mutable holder. Each recomposition creates a new local variable/reference cell. The once-remembered launcher assigns the initial cell while rememberLauncherForActivityResult updates to a callback capturing the latest cell.

## Impact and preconditions
After recomposition while the save sheet is open, source is null and the write branch is skipped; onResult still returns KmpFile(uri). ByteArray and KmpFile exports can silently produce zero-byte documents. Pending sources also lack a process-recreation policy and are not cleared.

## Supporting evidence
- The Kotlin capture structure is directly visible at lines 32,42,65-73.
- Unmerged upstream commit be274cc530ff92e6e3bde9ac0ffbb912d5e3068a independently describes this exact recomposition defect and adds host tests; those tests were not run here.

## Recommended solution
Store a PendingSaveRequest in a remembered state/holder shared by launch and callback. Consume and clear exactly once; define process-death recovery separately for URI and in-memory payloads; fail/clean up rather than returning success when required content is unavailable.

## Risks and compatibility
Do not put large ByteArrays in saved-instance Bundle state. Serialize concurrent launch attempts, and distinguish intentional null/empty content from lost pending state.

## Required tests / acceptance criteria
- Compose/Robolectric launch, recompose, then result for bytes and KmpFile
- Activity recreation with pending URI and ByteArray
- Cancel clears payload
- Repeated/concurrent launch policy
- No-op write cannot report success

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/551
- https://github.com/MohamedRejeb/Calf/commit/be274cc530ff92e6e3bde9ac0ffbb912d5e3068a
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
