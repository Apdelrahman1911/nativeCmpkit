# [Medium][IO-006] Save write failures can report success or escape without a completion/error result

<!-- nativecmpkit-item:audit:IO-006 -->
## Classification
- **Finding:** IO-006
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/picker/FileSaverLauncher.android.kt:42-60`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/androidMain/kotlin/com/mohamedrejeb/calf/picker/FileSaverLauncher.android.kt#L42-L60) — `save result IO`
- [`calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FileSaverLauncher.ios.kt:80-88,119-123`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/FileSaverLauncher.ios.kt#L80-L88) — `launchWithData/writeTempFile`
- [`calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/FileSaverLauncher.desktop.kt:32-45,49-62`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/FileSaverLauncher.desktop.kt#L32-L45) — `save coroutines`
- [`calf-file-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/picker/FileSaverLauncher.kt:8-18`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/commonMain/kotlin/com.mohamedrejeb.calf/picker/FileSaverLauncher.kt#L8-L18) — `result-only contract`

## Root cause
Android uses nullable stream ?.use chains and unconditionally emits KmpFile(uri) even when opening a stream returned null. iOS ignores NSData.writeToURL Boolean and returns its URL regardless. IO exceptions in remembered coroutine scopes have no common error channel/terminal-result policy.

## Impact and preconditions
Callers may show successful exports for unwritten content, present a picker for nonexistent staging, or remain waiting when failures escape. Partial created documents are not systematically rolled back. A cancellation result cannot communicate a provider/disk failure.

## Supporting evidence
- Android lines 47,52-53 skip failed opens but line 60 still emits a file.
- iOS line 122 ignores the only success result.
- The unmerged PR #551 introduces onError overloads and staging checks; baseline has neither.

## Recommended solution
Check every open/write/copy result, close resources, remove only newly created owned partial files on failure, and add backward-compatible typed onError/result overloads. Keep cancellation distinct and rethrow coroutine cancellation rather than converting it to a generic error.

## Risks and compatibility
Do not delete an existing user-selected destination when cleanup ownership is unknown. Existing callbacks may rely on current null behavior, so document migration semantics.

## Required tests / acceptance criteria
- Resolver returns null input/output stream
- Permission revoked during read/write
- Disk-full and failing close
- iOS writeToURL returns false
- Cancellation during copy
- Exactly one terminal event for success/cancel/error

## Dependencies
- IO-002
- IO-004
- IO-005

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/551
- https://github.com/MohamedRejeb/Calf/commit/1a20b60
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
