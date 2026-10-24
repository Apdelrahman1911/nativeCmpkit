# [Medium][NATIVE-028] Android file sharing forwards file:// URIs without FileProvider conversion

<!-- nativecmpkit-item:audit:NATIVE-028 -->
## Classification
- **Finding:** NATIVE-028
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-share`, `calf-io`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-share/src/androidMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.android.kt:65-85`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/androidMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.android.kt#L65-L85) — `createFileShareIntent/createMultipleFilesShareIntent`
- [`calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFile.android.kt:8-10,59-62`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFile.android.kt#L8-L10) — `KmpFile constructor/File.toKmpFile`

## Root cause
Sharing forwards KmpFile.uri directly into EXTRA_STREAM with a read flag. Public KmpFile accepts arbitrary Uri and java.io.File.toKmpFile explicitly constructs Uri.fromFile; that file:// path is not made shareable by FLAG_GRANT_READ_URI_PERMISSION.

## Impact and preconditions
A natural File.toKmpFile→ShareContent.File path fails on modern Android with file URI exposure or an unreadable recipient path, instead of sharing. Android catch usually reduces the launch failure to Unavailable with no diagnostic.

## Supporting evidence
- KmpFile.android.kt File.toKmpFile returns Uri.fromFile(this).
- Share construction does no URI scheme check/conversion before creating ACTION_SEND/ACTION_SEND_MULTIPLE.

## Recommended solution
Require/validate content URIs or convert library-owned local files through an explicitly configured FileProvider before launching. Preserve document-provider URI grants and avoid granting write/all-cache access unnecessarily; surface meaningful failure.

## Risks and compatibility
The API also correctly supports content:// KmpFiles. Do not blanket-copy arbitrary provider files or broaden grants merely to support file://. Device intent behavior still requires instrumented validation.

## Required tests / acceptance criteria
- Internal File.toKmpFile on API24+ produces a recipient-readable content URI.
- SAF photo/document URIs retain least-privilege read access and correct multi-file ClipData/extra grants.
- Revoked/ungrantable URI, empty list, mixed MIME and provider exceptions.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/508
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
