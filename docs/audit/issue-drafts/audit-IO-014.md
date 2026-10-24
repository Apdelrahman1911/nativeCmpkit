# [Medium][IO-014] Portable path/name metadata exposes encoded or unreadable references instead of the readable file

<!-- nativecmpkit-item:audit:IO-014 -->
## Classification
- **Finding:** IO-014
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-io`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-io/src/iosMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.ios.kt:18-24,45-57`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/iosMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.ios.kt#L18-L24) — `getName/getPath/isDirectory`
- [`calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFile.android.kt:40-51`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFile.android.kt#L40-L51) — `getName/getPath/isDirectory`
- [`calf-io/src/webMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.web.kt:15-17`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/webMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.web.kt#L15-L17) — `getName/getPath`
- [`calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.kt:26-40`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.kt#L26-L40) — `metadata contract`

## Root cause
iOS extracts a name by splitting originalUrl.absoluteString rather than lastPathComponent, retaining URL escapes. getPath also returns originalUrl.absoluteString rather than the path of its readable temp copy. Android returns URI strings and web returns only names under the same path API.

## Impact and preconditions
Names such as report%20one.pdf are not the expected human/file name; consumers passing getPath to a filesystem API can fail on file:// or content:// strings, inaccessible iOS originals, or ambiguous browser basenames. isDirectory may query a transient original instead of the readable URL.

## Supporting evidence
- iOS names and paths both derive from originalUrl.absoluteString despite the KmpFile docs warning it may be inaccessible.
- Current source() already avoids getPath on Android and uses url.path on iOS; this is the safe content access route.
- PR #551 e2ded9f/b82e19d implements a path-versus-URI distinction; not merged into baseline.

## Recommended solution
Separate URI serialization from optional filesystem paths; define platform guarantees in API docs, use NSURL.lastPathComponent for names and the readable copy for a filesystem path, and encourage source() for content instead of reverse-engineering paths.

## Risks and compatibility
Existing consumers may depend on URI-string getPath behavior. Introduce explicit toUriString/path APIs or a documented migration rather than silently changing all meanings. Preserve original display name when staging.

## Required tests / acceptance criteria
- Space, percent, Unicode and slash-escaped URL names
- Readable iOS temp-copy path after original expires
- Android content:// vs file://
- Two browser files with identical names
- Round-trip URI serialization independent of path

## Dependencies
- IO-008

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/551
- https://github.com/MohamedRejeb/Calf/issues/309
- https://github.com/MohamedRejeb/Calf/commit/b82e19d
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
