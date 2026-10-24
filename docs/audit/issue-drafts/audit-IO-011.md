# [Medium][IO-011] Web saver accepts onResult but never calls it or exposes download-only capability

<!-- nativecmpkit-item:audit:IO-011 -->
## Classification
- **Finding:** IO-011
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/src/webMain/kotlin/com.mohamedrejeb.calf/picker/FileSaverLauncher.web.kt:21-44,47-60`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/webMain/kotlin/com.mohamedrejeb.calf/picker/FileSaverLauncher.web.kt#L21-L44) — `rememberFileSaverLauncher/triggerDownload`
- [`calf-file-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/picker/FileSaverLauncher.kt:8-18`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/picker/FileSaverLauncher.kt#L8-L18) — `onResult contract`

## Root cause
The web implementation ignores onResult and only clicks a Blob-backed download anchor. The common API has no distinct StartedDownload result or capability indicator, while its callback is documented as saved-file or cancellation.

## Impact and preconditions
Cross-platform UI awaiting completion remains pending on every browser save. A downloaded Blob is not a filesystem-confirmed save, so reporting a made-up KmpFile success would be equally misleading.

## Supporting evidence
- onResult appears only in the function signature in the baseline web saver.
- PR #551/ff62e5b adds a real save path on supporting browsers but still explicitly cannot observe download completion on others.

## Recommended solution
Document and expose download-only versus verifiable-save capabilities. Add a real File System Access API save path where available and a distinct started-download event/fallback contract where completion cannot be observed, keeping old overloads compatible.

## Risks and compatibility
Browser support, secure contexts, user activation and iframe restrictions vary. Do not falsely equate anchor.click with persisted data, or return null cancellation merely because a download was initiated.

## Required tests / acceptance criteria
- Chromium File System Access success/cancel/error if added
- Safari/Firefox download fallback state transition
- Caller never waits for an unsupported terminal event
- User activation and insecure-context fallback
- JS/Wasm parity

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/551
- https://github.com/MohamedRejeb/Calf/commit/ff62e5b
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
