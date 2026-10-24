# [Medium][IO-019] Android folder selections are wrapped using single-document metadata and stream-based existence

<!-- nativecmpkit-item:audit:IO-019 -->
## Classification
- **Finding:** IO-019
- **Priority:** Medium
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-io`, `calf-file-picker`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/picker/FilePickerLauncher.android.kt:229-251`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/picker/FilePickerLauncher.android.kt#L229-L251) — `pickFolder/OpenDocumentTree`
- [`calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFile.android.kt:12-19,40-51`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFile.android.kt#L12-L19) — `exists/getName/isDirectory`

## Root cause
OpenDocumentTree results retain tree URIs but KmpFile metadata always uses DocumentFile.fromSingleUri, not fromTreeUri or a normalized tree document URI. exists attempts to open an InputStream, which is a content-readability operation rather than a directory existence test.

## Impact and preconditions
A successfully picked directory can be reported nonexistent, unnamed or not a directory on providers that do not support opening a tree URI as a stream or querying it as a single document. Exact provider behavior varies, so this finding is not labeled an instrumented Android failure.

## Supporting evidence
- Folder callback at 241 returns KmpFile(uri) unchanged.
- All metadata routes in KmpFile.android.kt use fromSingleUri; exists only tests openInputStream.

## Recommended solution
Recognize tree/document/file URI forms, use tree-aware metadata and existence queries, and separate directory capabilities from byte-stream capabilities. Preserve the original URI/grant for child enumeration.

## Risks and compatibility
DocumentFile.fromSingleUri accepts URIs without validating their semantic kind, so its construction alone does not prove a provider query succeeds. Provider exceptions and revoked grants need explicit handling.

## Required tests / acceptance criteria
- ExternalStorageProvider, Downloads and cloud-provider folder URIs
- Folder exists/name/isDirectory immediately and after restart
- Single-document and file:// regression tests
- Permission denial and unavailable provider

## Dependencies
- IO-008
- IO-010

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
