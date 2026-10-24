# [Medium][IO-008] Picked-file access lifetime is not represented for security-scoped folders or persisted Android URIs

<!-- nativecmpkit-item:audit:IO-008 -->
## Classification
- **Finding:** IO-008
- **Priority:** Medium
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-io`, `calf-file-picker`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.ios.kt:81-95,109-122,316-322`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FilePickerLauncher.ios.kt#L81-L95) — `folder results and asCopy=false`
- [`calf-io/src/iosMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.ios.kt:22-31,35-36,55-57`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/iosMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.ios.kt#L22-L31) — `raw NSURL wrappers/read/metadata`
- [`calf-io/src/iosMain/kotlin/com.mohamedrejeb.calf/io/KmpFileSource.ios.kt:9-11`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/iosMain/kotlin/com.mohamedrejeb.calf/io/KmpFileSource.ios.kt#L9-L11) — `source`
- [`calf-file-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/picker/FilePickerLauncher.android.kt:180-185,207-214,237-242`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/picker/FilePickerLauncher.android.kt#L180-L185) — `SAF URI results`

## Root cause
Folder selection returns an external NSURL directly and no operation in these modules balances start/stopAccessingSecurityScopedResource or models bookmarks. Android returns SAF/photo URIs without an opt-in persisted grant/bookmark abstraction. Common KmpFile does not express ownership or access expiry.

## Impact and preconditions
External folder/provider access and restored references can fail outside a callback/session or after process restart, despite metadata strings still existing. Nonfolder iOS picks are copied, reducing but not eliminating lifetime concerns for manually wrapped or exported URLs. Exact behavior depends on provider and OS.

## Supporting evidence
- Baseline iOS folder branch uses KmpFile(nsUrl) and forOpeningContentTypes asCopy=false.
- No startAccessingSecurityScopedResource or takePersistableUriPermission call is present in the audited baseline modules.
- PR #551/c70d35c is unmerged prior work on persisted bookmarks; platform consequences here are explicitly risk-classified.

## Recommended solution
Define explicit ephemeral versus owned versus persisted file handles. Add scoped-access helpers and opt-in bookmark/persistable-permission APIs with release/revocation handling; do not blanket-persist every selection. Document paths that are safe only while access is held.

## Risks and compatibility
Security scopes must be balanced on all exits and must remain active while streaming, not merely while opening. Persisting user permissions is a policy choice and should be explicit. Already sandbox-owned copies must not require successful scope acquisition.

## Required tests / acceptance criteria
- iCloud/third-party folder access after callback
- Stream open/read/close balances scope
- Android SAF grant release/revoke/restart
- iOS stale bookmark and access denial
- Sandbox-local file path
- Save destination reopened after callback

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/551
- https://github.com/MohamedRejeb/Calf/commit/c70d35c
- https://github.com/MohamedRejeb/Calf/issues/495
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
