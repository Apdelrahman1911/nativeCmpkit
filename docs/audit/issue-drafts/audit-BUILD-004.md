# [Medium][BUILD-004] Packaged native platform matrix omits Linux arm64 and Windows arm64 paths expected by loaders

<!-- nativecmpkit-item:audit:BUILD-004 -->
## Classification
- **Finding:** BUILD-004
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`, `calf-share`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`.github/workflows/build-native-libs.yml:20-180`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/.github/workflows/build-native-libs.yml#L20-L180) — `native platform build jobs`
- [`calf-file-picker/native/build-all-targets.sh:48-62`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/native/build-all-targets.sh#L48-L62) — `build_target matrix`
- [`calf-file-picker/build.gradle.kts:47-63`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/build.gradle.kts#L47-L63) — `nativeLibProps`
- [`calf-share/build.gradle.kts:38-54`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/build.gradle.kts#L38-L54) — `nativeLibProps`

## Root cause
CI produces macOS arm64/x64, Windows x64 and Linux x64 only. Host Gradle nativeLibProps supports Linux arm64, while native loaders also describe Windows arm64 resource paths; neither is produced by the baseline release pipeline.

## Impact and preconditions
An advertised generic desktop artifact does not contain matching native file-picker resources for these ARM hosts; manual system-library provisioning or a local build may be required. Share behavior differs by OS and must not be claimed equivalent to macOS sharing.

## Supporting evidence
- CI has three OS jobs and four target triples total
- build-all-targets.sh linux branch only invokes x86_64-unknown-linux-gnu

## Recommended solution
Publish a precise support matrix. Add native-arm64 builders/cross-compilation with load smoke tests where support is intended, or report unsupported architectures clearly before attempting native extraction.

## Risks and compatibility
Cross-compilation can produce binaries with incompatible glibc/SDK baselines even when compilation succeeds. Windows arm64 host matching and toolchain setup also need implementation work.

## Required tests / acceptance criteria
- Assert required resource paths against the documented supported-platform matrix
- Run JNI load and dialog cancellation tests on real Linux arm64 and Windows arm64 if claiming support
- Verify glibc/SDK minimum compatibility of produced binaries

## Dependencies
- BUILD-003

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/BUILD.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/BUILD.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
