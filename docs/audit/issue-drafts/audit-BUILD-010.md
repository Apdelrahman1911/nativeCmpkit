# [Low][BUILD-010] Desktop resource processing always invokes an untracked release-mode Cargo build

<!-- nativecmpkit-item:audit:BUILD-010 -->
## Classification
- **Finding:** BUILD-010
- **Priority:** Low
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`, `calf-share`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/build.gradle.kts:67-99`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/build.gradle.kts#L67-L99) — `buildNativeLib/copyNativeLib/resource dependency`
- [`calf-share/build.gradle.kts:58-88`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/build.gradle.kts#L58-L88) — `buildNativeLib/copyNativeLib/resource dependency`

## Root cause
Each native Exec task sets outputs.upToDateWhen { false }, declares no source/lock/toolchain inputs or output library, and is attached to desktopProcessResources. A local test or resource build therefore invokes cargo build --release even when native inputs are unchanged.

## Impact and preconditions
Gradle cannot skip/cache the native task, Rust becomes a prerequisite for JVM-only test work, and local builds do repeated process/toolchain/dependency-resolution work. Cargo may itself reuse compiled objects, so this is not a claim that every invocation recompiles all Rust code.

## Supporting evidence
- The explicit outputs.upToDateWhen { false } occurs in both module build scripts
- No Gradle native task inputs/outputs are declared in either task block

## Recommended solution
Declare target-specific inputs/outputs and lock/toolchain inputs; separate developer-host native builds, test fixtures and full release assemblies. Preserve correct rebuilds when JNI symbols or Rust source change.

## Risks and compatibility
Incorrect incremental inputs can silently ship stale binaries, which is worse than redundant work; implement alongside native manifest validation.

## Required tests / acceptance criteria
- Run identical desktop resource tasks twice and assert the native Gradle task is UP-TO-DATE or FROM-CACHE
- Modify Rust source, lockfile and toolchain independently and assert rebuilds
- Verify JVM unit tests can run without building irrelevant platform binaries

## Dependencies
- BUILD-003
- BUILD-005

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/BUILD.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/BUILD.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
