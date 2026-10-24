# [Medium][IO-009] Browser file reads treat DONE as success and do not cancel or propagate FileReader failures

<!-- nativecmpkit-item:audit:IO-009 -->
## Classification
- **Finding:** IO-009
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-io`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-io/src/jsMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.js.kt:11-28`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/jsMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.js.kt#L11-L28) — `readFileAsBytes`
- [`calf-io/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.wasmJs.kt:12-34`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.wasmJs.kt#L12-L34) — `readFileAsBytes/getResult`
- [`calf-io/src/webMain/kotlin/com.mohamedrejeb.calf/io/KmpFileSource.web.kt:7-8`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/webMain/kotlin/com.mohamedrejeb.calf/io/KmpFileSource.web.kt#L7-L8) — `source`

## Root cause
Both implementations use suspendCoroutine, only onloadend, and readyState==DONE as the success test. FileReader reaches DONE on errors/abort too; result can be null. They never inspect error, install onerror/onabort handlers, or abort the reader on coroutine cancellation.

## Impact and preconditions
Read failures can be returned as empty bytes (or fail in interop/callback code) instead of an exception, making corrupt/missing content indistinguishable from a valid empty file. Cancelled screen/request work continues reading and allocating the whole file; source() inherits the behavior.

## Supporting evidence
- Both files branch solely on readyState at their onloadend handler and call continuation.resume.
- FileReader DONE denotes completion rather than successful completion. No error or cancellation branch exists in the source.
- No real-browser FileReader failure was executed in this review.

## Recommended solution
Use a cancellable suspension with exactly-once completion, onload success handling, explicit error/abort propagation, cancellation-triggered FileReader.abort, and listener cleanup. Register handlers before starting the read.

## Risks and compatibility
Abort from cancellation must not cause a second resume. JS and Wasm interop need separate browser tests; a Node typed-array example alone would not prove compiled Kotlin browser behavior.

## Required tests / acceptance criteria
- Readable empty/nonempty files
- FileReader NotReadableError and SecurityError
- Abort before completion and after onload
- Dispose image request during large read
- Exactly one resume and handlers removed
- JS/Wasm parity

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
