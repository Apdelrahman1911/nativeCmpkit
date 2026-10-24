# [Medium][BUILD-005] Native release binaries have unlocked Rust dependencies and a floating compiler

<!-- nativecmpkit-item:audit:BUILD-005 -->
## Classification
- **Finding:** BUILD-005
- **Priority:** Medium
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`, `calf-share`, `CI`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/native/.gitignore:1-2`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/native/.gitignore#L1-L2) — `Cargo.lock exclusion`
- [`calf-share/native/.gitignore:1-2`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/native/.gitignore#L1-L2) — `Cargo.lock exclusion`
- [`calf-file-picker/native/Cargo.toml:9-16`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/native/Cargo.toml#L9-L16) — `dependency constraints`
- [`calf-share/native/Cargo.toml:9-16`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/native/Cargo.toml#L9-L16) — `dependency constraints`
- [`.github/workflows/build-native-libs.yml:26-39`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/.github/workflows/build-native-libs.yml#L26-L39) — `Rust toolchain and cache`

## Root cause
Both cdylib projects ignore Cargo.lock, dependencies use compatible ranges, CI installs dtolnay/rust-toolchain@stable and cargo build omits --locked. These are shipped binary inputs, not only source-library development constraints.

## Impact and preconditions
The same Git commit can produce different dependency graphs and binaries over time or from different registry caches. Vulnerability and license inventories cannot be tied reliably to a released native artifact.

## Supporting evidence
- Audit online cargo metadata resolved 197 file-picker packages and 48 share packages including roots
- 202 unique non-root name/version pairs were queried in OSV
- The first offline share resolution and subsequent online picker resolution selected different compatible versions of shared dependencies

## Recommended solution
Commit and maintain both Cargo.lock files, pin rust-toolchain.toml, build with --locked, include locks/toolchain/target in cache keys and retain per-target dependency/license/provenance manifests. Review lock updates rather than suppressing advisories globally.

## Risks and compatibility
A lockfile generated during this audit reflects 2026-10-24 resolution, not the original release graph. Do not present it as the historical shipped graph.

## Required tests / acceptance criteria
- Build one revision from empty caches twice and compare package graphs and reproducibility metadata
- Reject changed dependency resolution under --locked
- Verify CI uses the exact pinned Rust toolchain for every target

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/BUILD.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/BUILD.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
