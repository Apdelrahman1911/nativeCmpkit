# [Low][IO-022] Native cache fallback can lose user isolation and loader trusts external search paths

<!-- nativecmpkit-item:audit:IO-022 -->
## Classification
- **Finding:** IO-022
- **Priority:** Low
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/NativeLibLoader.kt:18-22,34-42,66-69`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/NativeLibLoader.kt#L18-L22) — `loadNativeLibrary/userCacheDir`
- [`calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/NativeLibCache.kt:46-62`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/NativeLibCache.kt#L46-L62) — `extractNativeLibrary/hasIdenticalContent`

## Root cause
When user.home is absent the fixed .cache/calf-filepicker directory is placed under java.io.tmpdir, potentially shared with other users. mkdirs and reads follow existing filesystem entries without ownership/symlink validation, and verification/load are separated. System.loadLibrary is intentionally tried first without an ABI/content check.

## Impact and preconditions
In nondefault deployments with attacker-writable cache/search-path components, a local attacker may race or substitute executable native code. Normal private-home usage reduces the threat substantially; truncated SHA-256 naming is cache isolation, not an authenticity guarantee. No compromise was reproduced.

## Supporting evidence
- The fallback at loader line 68 selects java.io.tmpdir but appends a fixed directory, not a unique private directory.
- Baseline verifies existing bytes and uses unique temp files/atomic move with fallback; positive cache probes passed.
- System-library-first behavior was deliberately added by 6331db2 for packagers and is not inherently a vulnerability.
- The separate share-cache issue NATIVE-031 uses a constant target name; it is not the same bug as this picker hardening risk. Picker content-addressing is an existing remediation reference for share.

## Recommended solution
Create a private randomized fallback directory with restrictive permissions, validate cache ownership/no-follow policy, document trusted java.library.path deployment requirements, and consider ABI version negotiation for externally packaged libraries. Retain the safe identical-content reuse fix.

## Risks and compatibility
A same-user attacker often already controls the process; do not exaggerate this as remote code execution. OS signing/quarantine and Windows loaded-DLL behavior must remain compatible. Cache names retain upstream identifiers intentionally for binary compatibility.

## Required tests / acceptance criteria
- Missing user.home with shared temp directory
- Precreated symlink/foreign-owned cache directory
- Concurrent extraction and failed move
- Mismatched native ABI from system path
- Windows loaded-DLL reuse
- Read-only home/noexec mount errors

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/commit/6331db2
- https://github.com/MohamedRejeb/Calf/commit/befc455
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/IO.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/IO.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
