# [Medium][IO-020] Android whole-file read leaks its input stream if reading fails

<!-- nativecmpkit-item:audit:IO-020 -->
## Classification
- **Finding:** IO-020
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-io`, `calf-file-picker-coil`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFile.android.kt:30-37`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/androidMain/kotlin/com/mohamedrejeb/calf/io/KmpFile.android.kt#L30-L37) — `KmpFile.readByteArray`

## Root cause
inputStream.close runs in also after readBytes returns successfully; no use/finally surrounds the read. A provider read exception bypasses closure.

## Impact and preconditions
Failing cloud/provider streams can retain file descriptors and remote provider resources. Repeated image loads through KmpFileFetcher can accumulate leaked resources.

## Supporting evidence
- readBytes().also { inputStream.close() } at lines 35-37 has no exceptional cleanup.
- The streaming source() returns an owned RawSource with explicit caller-close documentation; this finding targets readByteArray, not that ownership contract.

## Recommended solution
Wrap openInputStream in use and return the read from inside it, preserving primary exceptions and ensuring the stream closes on read/close failure. Prefer streaming where consumers support it.

## Risks and compatibility
Closure must occur exactly once and preserve read exceptions with suppressed close failures. Cancellation alone does not interrupt every blocking InputStream.

## Required tests / acceptance criteria
- InputStream throws after partial bytes and close count is one
- Successful and empty reads close once
- close itself throws
- Null resolver stream still reports not found
- Coil failed-fetch path

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
