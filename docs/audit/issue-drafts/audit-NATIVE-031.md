# [Medium][NATIVE-031] Desktop native share extraction uses one mutable filename across versions, architectures and processes

<!-- nativecmpkit-item:audit:NATIVE-031 -->
## Classification
- **Finding:** NATIVE-031
- **Priority:** Medium
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-share`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/platform/NativeLibLoader.kt:47-84`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/desktopMain/kotlin/com/mohamedrejeb/calf/share/platform/NativeLibLoader.kt#L47-L84) — `cache directory/extraction/System.load`

## Root cause
Resources are OS/architecture-specific but every version/architecture extracts into the same per-user basename. Atomic move prevents partially written files, but there is no lock or immutable content-addressed identity between move and System.load. mkdirs results/ownership/symlink constraints are not validated.

## Impact and preconditions
Concurrent JVMs or versions may load the other process artifact; architecture changes can collide. Windows can refuse replacing a DLL already loaded by another process, forcing a fallback. A writable/redirected cache/system library path is a trust boundary, but same-user control alone is not a demonstrated privilege escalation.

## Supporting evidence
- ResourcePath includes osPart/archPart at47; targetFile uses only libFileName at60.
- Source performs mutable rename then loads path at84 with no intervening identity check.
- calf-file-picker has a newer immutable content-hashed NativeLibCache (commit befc455); the equivalent share loader was not migrated to that cache strategy.

## Recommended solution
Use version/OS/architecture/content-digest immutable filenames in a verified private cache directory; validate bytes/path, extract atomically without overwriting loaded versions, and document cleanup. Preserve intentional System.loadLibrary-first support for external packagers as an explicit trusted override. Reuse/adapt the content-addressed NativeLibCache already implemented in calf-file-picker rather than duplicating a new extraction design.

## Risks and compatibility
No wrong-binary or arbitrary-code execution was performed. The move-to-load race and Windows replacement outcome depend on concurrent launches/platform rules; cache and native library trust should be tested without claiming an exploitable CVE.

## Required tests / acceptance criteria
- Two versions/architectures race between extraction and loading and each receives its own digest.
- Concurrent Windows process with loaded DLL does not lose native functionality.
- Read-only home, failed mkdirs, symlinked cache, interrupted extraction, no resource and trusted external packager library.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/commit/6331db22d2018c1a1ea2b52a291da2d8ee78138d
- https://github.com/MohamedRejeb/Calf/commit/befc455
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
