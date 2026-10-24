# [High][BUILD-003] Any nonempty prebuilt native subdirectory suppresses every local native build

<!-- nativecmpkit-item:audit:BUILD-003 -->
## Classification
- **Finding:** BUILD-003
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`, `calf-share`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/build.gradle.kts:33-39`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/build.gradle.kts#L33-L39) — `hasPrebuiltNativeLibs`
- [`calf-share/build.gradle.kts:29-33`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/build.gradle.kts#L29-L33) — `hasPrebuiltNativeLibs`

## Root cause
The prebuilt predicate accepts any nonempty immediate directory. It does not check the host target, expected library filename, source revision, JNI ABI, package version, checksum, or complete publication platform matrix.

## Impact and preconditions
A partial/stale/foreign-platform artifact folder silently bypasses Rust compilation and is packaged as trusted resources. Desktop consumers can fail with missing native libraries or receive binaries unrelated to the checked-out Kotlin/Rust source. This is an integrity/release-readiness defect, not evidence of malicious binaries.

## Supporting evidence
- The exact predicates contain only exists/isDirectory/listFiles().isNotEmpty checks
- The Rust build/copy tasks are entirely absent when the predicate is true

## Recommended solution
Introduce a native artifact manifest keyed by module, target, source revision and ABI/version; validate required filenames and checksums before skipping a build. Use explicit developer-host vs release-matrix tasks and fail closed for incomplete release inputs.

## Risks and compatibility
Must preserve offline/prebuilt developer workflows and distinguish source builds from full release assemblies. A checksum manifest must itself be tied to trusted CI provenance.

## Required tests / acceptance criteria
- Test empty, irrelevant-file-only, wrong-platform, corrupt, stale-revision and missing-library directories
- Verify full artifact manifests before assembling candidate desktop JARs
- Load each candidate binary and check JNI symbol compatibility on its intended host

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/BUILD.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/BUILD.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
