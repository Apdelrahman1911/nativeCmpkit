# [Medium][BUILD-007] Dependency and workflow trust is not reproducibly verified beyond the wrapper

<!-- nativecmpkit-item:audit:BUILD-007 -->
## Classification
- **Finding:** BUILD-007
- **Priority:** Medium
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `build tooling`, `CI`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`settings.gradle.kts:3-22`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/settings.gradle.kts#L3-L22) — `plugin and dependency repositories`
- [`convention-plugins/build.gradle.kts:22-30`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/convention-plugins/build.gradle.kts#L22-L30) — `build-time plugin dependencies`
- [`.gitignore:73-75`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/.gitignore#L73-L75) — `kotlin-js-store exclusion`
- [`.github/workflows/mkdocs.yml:12-24`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/.github/workflows/mkdocs.yml#L12-L24) — `unpinned actions and pip installs`
- [`.github/workflows/build-native-libs.yml:24-39`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/.github/workflows/build-native-libs.yml#L24-L39) — `mutable action references`

## Root cause
No Gradle dependency verification metadata or dependency locks are tracked; generated Kotlin JS lock storage is ignored; workflow actions use mutable tags; MkDocs installs unconstrained packages. HTTPS and version pins alone do not authenticate all build inputs or freeze transitive graphs.

## Impact and preconditions
Future builds can execute changed third-party plugin/action/install code or resolve different transitive dependencies. This is a supply-chain risk; the audit found no evidence of a compromised build input.

## Supporting evidence
- Wrapper JAR and distribution hashes DO match official Gradle 9.7.1: this is a positive control, not a wrapper vulnerability
- 548 baseline text-like files passed a narrow secret-marker scan; it was not a full historical or entropy-based secret audit
- docs/testing/evidence/registry-version-checks.json and baseline-secret-marker-scan.json

## Recommended solution
Maintain Gradle verification metadata and dependency locks, track generated JS package-manager locks with frozen installs, pin actions to reviewed full SHAs, lock Python tooling, and add dependency/license/SBOM review. Keep pull-request workflows read-only and publication credentials in owner-gated protected environments.

## Risks and compatibility
Verification bootstrap must use independently trusted artifacts; auto-accepting every new checksum defeats the control. Locking all KMP target graphs requires cross-platform CI coordination.

## Required tests / acceptance criteria
- Reject an intentionally modified downloaded build artifact in a local verification fixture
- Check frozen JS/Python dependency installation from empty caches
- Validate action SHA updates and least-privilege workflow permissions
- Re-run full resolved-graph security scans after dependency updates

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/BUILD.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/BUILD.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
