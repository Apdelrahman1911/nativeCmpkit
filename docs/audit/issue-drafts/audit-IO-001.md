# [High][IO-001] iOS byte-array reads can overrun native destination memory and mishandle empty files

<!-- nativecmpkit-item:audit:IO-001 -->
## Classification
- **Finding:** IO-001
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-io`, `calf-file-picker-coil`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-io/src/iosMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.ios.kt:35-41`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-io/src/iosMain/kotlin/com.mohamedrejeb.calf/io/KmpFile.ios.kt#L35-L41) — `KmpFile.readByteArray`
- [`calf-file-picker-coil/src/commonMain/kotlin/com.mohamedrejeb.calf/picker/coil/KmpFileFetcher.kt:22-27`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker-coil/src/commonMain/kotlin/com.mohamedrejeb.calf/picker/coil/KmpFileFetcher.kt#L22-L27) — `KmpFileFetcher.fetch`

## Root cause
The ByteArray allocation clamps NSData.length to Int.MAX_VALUE, but memcpy still receives the original, larger length. The zero-length case unconditionally calls addressOf(0).

## Impact and preconditions
For a file larger than Int.MAX_VALUE whose allocations succeed, native writes exceed the Kotlin buffer. Empty data violates the element-address precondition. Coil reaches this path too. This is memory-unsafety in source, not a demonstrated device exploit.

## Supporting evidence
- Baseline lines 37 and 40 use different allocation/copy lengths. No guard precedes addressOf(0).
- Linux cannot execute Foundation or Kotlin/Native iOS behavior. The unsafe arithmetic is source-confirmed.
- The archived PR #551 branch retains this memcpy pattern; its other IO changes do not fix this finding.

## Recommended solution
Return immediately for length zero, reject lengths exceeding the representable ByteArray limit before allocating, copy exactly the validated allocation size, and prefer source() for large content. Make NSData read failure an explicit error.

## Risks and compatibility
Native bounds fixes must preserve byte signedness and all platforms' exception contracts. Large-file tests must not exhaust devices; use a checked-length helper and controlled native fixtures.

## Required tests / acceptance criteria
- Zero-byte valid file
- One-byte and binary round trips
- Length helper at Int.MAX_VALUE and Int.MAX_VALUE+1 without huge allocations
- Missing/unreadable file errors
- ASan/native guarded-buffer integration where supported
- Coil error propagation

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/551
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
