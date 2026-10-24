# [Medium][NAV-014] Streaming sample cancellation does not interrupt its synchronous read loop

<!-- nativecmpkit-item:audit:NAV-014 -->
## Classification
- **Finding:** NAV-014
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `sample:common`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/FilePickerScreen.kt:88-103`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/FilePickerScreen.kt#L88-L103) — `streamingJob cancellation`
- [`sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/FilePickerScreen.kt:313-345`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/common/src/commonMain/kotlin/com.mohamedrejeb.calf.sample/screens/FilePickerScreen.kt#L313-L345) — `describeStreaming/countBytes`

## Root cause
Replacing a selection cancels the old job, but countBytes loops over synchronous RawSource reads without suspension or checking coroutine cancellation. withContext(Default) and catching/rethrowing CancellationException do not inject a check inside that loop.

## Impact and preconditions
A cancelled or no-longer-visible sample operation can continue consuming CPU/storage until EOF or I/O failure. The surrounding use correctly closes the source on exit; this finding is delayed cancellation, not a confirmed never-close leak.

## Supporting evidence
- All source locations refer to immutable baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- cancel at line93 is not observed inside while(true) lines339-344.
- use at line319 and explicit CancellationException rethrow at321-322 are positive existing cleanup behavior.
- PR545 introduced the demo; its own description notes browsers still load whole files while the KDoc lines313-315 says the file never needs to fit in memory.

## Recommended solution
Make the loop cancellation-cooperative with an explicit coroutine-context check per bounded chunk and test with a deliberately slow source. Document that the browser RawSource path currently buffers the whole Blob before the sample loop; fixed read chunks do not make that platform constant-memory.

## Risks and compatibility
An OS read may itself be uninterruptible; checking before chunks limits delay but is not a hard real-time cancellation guarantee. Browser buffering belongs to the I/O implementation audit.

## Required tests / acceptance criteria
- Slow fake source counts reads after cancellation and proves prompt termination/close.
- Reselect a file and leave the screen while counting; old work stops and does not overwrite new results.
- Run large native/JVM input with a defined cancellation latency bound.
- Correct sample memory claims for JS/Wasm buffering.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/545
- https://github.com/MohamedRejeb/Calf/issues/537
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NAV.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NAV.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
