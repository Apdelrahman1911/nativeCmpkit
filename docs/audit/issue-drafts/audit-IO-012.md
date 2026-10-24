# [Medium][IO-012] Immediate web Blob URL revocation can race the browser download

<!-- nativecmpkit-item:audit:IO-012 -->
## Classification
- **Finding:** IO-012
- **Priority:** Medium
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/src/webMain/kotlin/com.mohamedrejeb.calf/picker/FileSaverLauncher.web.kt:51-60`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/webMain/kotlin/com.mohamedrejeb.calf/picker/FileSaverLauncher.web.kt#L51-L60) — `triggerDownload`

## Root cause
triggerDownload revokes the object URL synchronously immediately after anchor.click and removing the anchor, assuming the browser has already consumed the Blob.

## Impact and preconditions
Browsers that resolve the download after the click returns can see a revoked URL and fail or create no download. This is a source-confirmed lifetime hazard with upstream Safari corroboration, but no Safari/WebKit run was available here.

## Supporting evidence
- Baseline invokes revokeObjectURL at line 60 in the same synchronous function as click at 58.
- Archived unmerged commit 66e345a9b291d4d82aa76b1f5f0d05e99b1bb8e1 describes Safari failures and uses deferred revocation.

## Recommended solution
Retain the URL until a documented safe deferred revocation point or platform-supported completion signal, and clean it up on exceptions. Keep a bounded lifecycle strategy rather than leaking every download URL.

## Risks and compatibility
There is no universal anchor-download completion signal. A delay is a pragmatic fallback, not proof of save completion; large downloads and background tabs must be tested.

## Required tests / acceptance criteria
- Safari macOS and iOS small/large downloads
- Chrome/Firefox unaffected positive paths
- Repeated downloads and URL retention bounds
- Anchor/create/click failure cleanup

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/551
- https://github.com/MohamedRejeb/Calf/commit/66e345a9b291d4d82aa76b1f5f0d05e99b1bb8e1
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
