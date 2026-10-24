# [Low][BUILD-011] Release staging duplicates both native libraries into both desktop artifacts

<!-- nativecmpkit-item:audit:BUILD-011 -->
## Classification
- **Finding:** BUILD-011
- **Priority:** Low
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `CI`, `calf-file-picker`, `calf-share`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`.github/workflows/build-native-libs.yml:66-79`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/.github/workflows/build-native-libs.yml#L66-L79) — `combined macOS artifact staging`
- [`.github/workflows/build-native-libs.yml:117-128`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/.github/workflows/build-native-libs.yml#L117-L128) — `combined Windows artifact staging`
- [`.github/workflows/deploy.yml:54-88`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/.github/workflows/deploy.yml#L54-L88) — `duplicated artifact downloads`
- [`.github/workflows/gradle.yml:85-119`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/.github/workflows/gradle.yml#L85-L119) — `snapshot artifact downloads`

## Root cause
Each native-libs-<os> artifact contains both picker and share binaries, and the complete artifact is downloaded into both modules resources/native directories without filtering.

## Impact and preconditions
Both desktop JAR resource trees contain unrelated native binaries, increasing artifact size and duplicating classpath resource paths. This also accidentally satisfies the permissive prebuilt detector when only the unrelated library is available.

## Supporting evidence
- build-native-libs.yml copies both libcalf_filepicker_native and libcalf_share_native into one native-libs tree
- Both publication workflows download each same named artifact twice into different module roots

## Recommended solution
Upload per-module native artifacts or filter each download against an explicit module manifest. Add expected-resource-path and archive-size checks before any future publication.

## Risks and compatibility
Changes must keep all required target binaries while avoiding accidental removal of dependent resources. Baseline workflows are disabled during migration; do not recreate the staging bug in replacement release automation.

## Required tests / acceptance criteria
- Inspect candidate picker/share JARs and assert only that module native library paths are included
- Assert no duplicate library resources across the two artifact manifests
- Test missing-module artifacts fail the prebuilt check

## Dependencies
- BUILD-003

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/BUILD.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/BUILD.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)

## Migration remediation (baseline finding retained)
The active release/snapshot staging workflows that copied both crate libraries into each module have been removed. Current native verification compiles the crates separately and never stages or publishes library packages.

Verification files:
- .github/workflows/build-native-libs.yml
- docs/migration/legacy/workflows/deploy.yml
- docs/testing/evidence/github-actions/native-log-40106895492.txt

Remaining caution: Future release packaging must include per-module/per-platform content assertions under BUILD-006; no future publication pipeline is certified.
