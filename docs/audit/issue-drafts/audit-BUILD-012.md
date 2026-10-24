# [Low][BUILD-012] Resolved Linux picker graph contains three newly unmaintained D-Bus crates

<!-- nativecmpkit-item:audit:BUILD-012 -->
## Classification
- **Finding:** BUILD-012
- **Priority:** Low
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-file-picker`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-file-picker/native/Cargo.toml:10-12`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-file-picker/native/Cargo.toml#L10-L12) — `rfd transitive dependency graph`

## Root cause
Audit-time resolution of rfd 0.15.4 uses the XDG portal/ashpd/zbus graph containing zvariant 5.15.1, zvariant_derive 5.15.1 and zbus_names 4.3.5. RustSec marks these standalone crates unmaintained after consolidation into zbus 6.

## Impact and preconditions
This is a maintenance warning, NOT a confirmed exploitable vulnerability and not proof of the dependency versions in any historical Calf binary. Future fixes may require moving rfd/ashpd/zbus together rather than a direct crate override.

## Supporting evidence
- 202 exact non-root Rust name/version pairs were queried; three matches were informational unmaintained advisories only
- docs/testing/evidence/osv-resolved-rust-query.json
- docs/testing/evidence/advisory-RUSTSEC-2026-0370.json, advisory-RUSTSEC-2026-0371.json, advisory-RUSTSEC-2026-0372.json

## Recommended solution
Track rfd portal-stack upgrades and their platform requirements, test a maintained dependency chain, and document/triage informational advisories separately from security vulnerabilities. Retain exact lock/provenance data for candidate releases.

## Risks and compatibility
Forcing incompatible zbus major versions through transitive overrides can break compilation or portal behavior. Preserve GTK/XDG portal behavior and cancellation semantics.

## Required tests / acceptance criteria
- Re-run OSV/RustSec on pinned complete Rust graphs
- Exercise portal file open/save/folder/multiple selection and cancellation on Linux
- Verify supported desktop/session bus environments and any new compiler requirements

## Dependencies
- BUILD-005

## Historical context
- https://rustsec.org/advisories/RUSTSEC-2026-0370.html
- https://rustsec.org/advisories/RUSTSEC-2026-0371.html
- https://rustsec.org/advisories/RUSTSEC-2026-0372.html
- https://github.com/z-galaxy/zbus/issues/2043
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/BUILD.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/BUILD.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
