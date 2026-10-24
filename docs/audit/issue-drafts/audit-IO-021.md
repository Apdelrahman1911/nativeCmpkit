# [Medium][IO-021] Coil fetches eagerly copy whole files and the byte-array API needs explicit scheduling/size guidance

<!-- nativecmpkit-item:audit:IO-021 -->
## Classification
- **Finding:** IO-021
- **Priority:** Medium
- **Evidence status:** `improvement` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker-coil`, `calf-io`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker-coil/src/commonMain/kotlin/com.mohamedrejeb.calf/picker/coil/KmpFileFetcher.kt:22-32`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker-coil/src/commonMain/kotlin/com.mohamedrejeb.calf/picker/coil/KmpFileFetcher.kt#L22-L32) — `fetch`
- [`calf-io/src/desktopMain/kotlin/com/mohamedrejeb/calf/io/KmpFile.desktop.kt:12`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/desktopMain/kotlin/com/mohamedrejeb/calf/io/KmpFile.desktop.kt#L12) — `readByteArray`
- [`calf-io/src/iosMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.ios.kt:35-41`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/iosMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.ios.kt#L35-L41) — `readByteArray`
- [`calf-io/src/webMain/kotlin/com.mohamedrejeb.calf/io/KmpFileSource.web.kt:7-8`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/webMain/kotlin/com.mohamedrejeb.calf/io/KmpFileSource.web.kt#L7-L8) — `eager web source`
- [`calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.kt:18-24,73-82`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.kt#L18-L24) — `readByteArray docs`

## Root cause
Fetcher always materializes a ByteArray then copies it into an Okio Buffer before decoding, despite native streaming IO now being available. readByteArray is suspend but performs blocking IO on Android/iOS/Desktop without dispatcher switching. Web source is intentionally buffered; iOS also materializes NSData before ByteArray.

## Impact and preconditions
Large media produce multiple encoded-data copies plus decoder allocations, increasing latency and OOM pressure. UI callers may assume suspend means nonblocking even though source() alone documents dispatcher ownership. MEMORY labeling and lack of a supplied stable KmpFile cache key also merit integration tests.

## Supporting evidence
- Fetcher lines 25-26 allocate through readByteArray and then Buffer.write.
- source() implementation and docs explicitly provide native streaming while web remains whole-buffer.
- No heap benchmark or complete Coil runtime test was run, so this is an improvement with quantified benchmarks required, not a measured regression.

## Recommended solution
Add native streaming adapters/URI or file mappers to Coil (or the official kotlinx-io/Okio bridge) with correct close/cancellation ownership; keep a bounded browser fallback. Document readByteArray blocking/size semantics, add decode-size guidance, and verify dataSource/keying behavior with Coil rather than inferring it.

## Risks and compatibility
Changing fetchers may affect EXIF, seek requirements, caching and thread selection. Do not label intended read-all behavior a security vulnerability; source() is already available for large-file consumers.

## Required tests / acceptance criteria
- Large image peak-memory benchmark by target
- Decoder failure closes source
- Coil cancellation closes provider stream
- Stable request key and modified-file invalidation policy
- Main-thread misuse guidance test/sample
- Binary content parity

## Dependencies
- IO-001
- IO-020

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/537
- https://github.com/MohamedRejeb/Calf/issues/537#issuecomment-5653462009
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
