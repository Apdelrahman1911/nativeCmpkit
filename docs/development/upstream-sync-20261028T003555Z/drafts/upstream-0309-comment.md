<!-- nativecmpkit-upstream-sync:674932206:309 -->
<!-- source-fingerprint:2d946252067d88f3034106c33c6678e27e3274c9956eb1df17dd5edb162a7bf7 -->
## Current upstream context: Calf #309

Original: [firebase compatibility](https://github.com/MohamedRejeb/Calf/issues/309) — [Puskistolero92](https://github.com/Puskistolero92); created `2025-05-27T16:08:46Z`, updated `2025-05-27T16:08:46Z`; upstream state **open**.
Original IDs: `3094469573` / `I_kwDOKDql7s64cdvF`. Original labels: None.

This comment preserves attributed public upstream material. It does not impersonate the original author, replace this issue's technical body, or transplant GitHub authorship/timestamps.

### Reconciled disposition
Still relevant; tracked by the existing nativeCmpkit finding rather than a duplicate issue.

KmpFile is a platform handle, not a portable Firebase filesystem path. readByteArray and source are available, but mobile URI/path metadata and eager-buffer guidance are already audited. Firebase integration itself is a consumer adapter/documentation question, not a confirmed Firebase defect.

**Next step:** Add an integration recipe distinguishing Android URI, iOS readable copy and byte/stream upload; keep Firebase out of core dependencies and link IO-014/IO-021.

Primary tracking: #51. Related existing tickets: #57.
**Lifecycle:** keep the existing nativeCmpkit issue state and unrelated labels/content unchanged. Do not close a broader remaining bug because an old upstream symptom is source-addressed.

### Current-source assessment locations
- [`calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.kt:8-126`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.kt#L8-L126) — `KmpFile metadata and byte reads`
- [`calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/KmpFileSource.kt:1-40`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/KmpFileSource.kt#L1-L40) — `RawSource API`

### Original issue description (verbatim Markdown)
````markdown
is there any way to upload the file to firebase storage? the file is created as KMPFile and I can only do readByteArray but to do the update in the database I can only do putData() or putFile().
````

### Original public discussion (0 comments)
No public conversation comments were returned in this snapshot.

### Relevant history and immutable evidence
- [Fresh original issue record](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261028T003555Z/source/issues/309/detail.json)
- [Full original comments](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261028T003555Z/source/issues/309/comments.json)
- [Full public timeline: 1 entries](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261028T003555Z/source/issues/309/timeline.json)
- [Verified snapshot receipt](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261028T003555Z/receipt.json) and [SHA256SUMS](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261028T003555Z/SHA256SUMS)
- Earlier original edit diffs, release/PR history and available attachment copies remain in `docs/migration/upstream-metadata/`; that frozen archive was not rewritten.
- `2026-10-24T16:17:40Z`: `cross-referenced` by [Apdelrahman1911](https://github.com/Apdelrahman1911) ([event](https://github.com/MohamedRejeb/Calf/issues/309)); [[Medium][IO-014] Portable path/name metadata exposes encoded or unreadable references instead of the readable file](https://github.com/Apdelrahman1911/nativeCmpkit/issues/51).
