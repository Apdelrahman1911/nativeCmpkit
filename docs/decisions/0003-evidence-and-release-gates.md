# ADR 0003 — Evidence classes and release gates

**Status:** adopted for this migration/audit, 2026-10-24.

## Context

The library spans common Kotlin, Compose, Android/JVM, UIKit/Objective-C, JNI/Rust,
JavaFX and browser JS/Wasm. A declaration, source scan, compiler success, standalone
probe and device test answer different questions. The initial audit environment
also had storage/toolchain limitations. Treating any green command as universal
platform validation would hide the most consequential integration risks.

GitHub issues/reviews and Git commits likewise have different identity models.
Recreating an issue cannot transfer original authorship, timestamps or discussion
relationships; archival fidelity and present-day actionability need separate records.

## Decision

1. Preserve an immutable upstream source baseline and exact raw GitHub metadata.
   Cite baseline code locations in findings, with real binary-asset hashes where
   line numbers do not exist. New findings/resolutions do not rewrite old evidence.
2. Classify evidence as source-confirmed, scoped test-confirmed, risk, unverified
   or improvement. Classify priority independently. Never infer an exploit,
   performance improvement or supported platform from an unrelated result.
3. Maintain separate ledgers for original tests, tests with explicit adapters,
   defect-confirmation probes, build/configuration/POM checks, native compilation,
   runtime/device integration and documentation/archive verification.
4. Record command, revision/worktree deviations, dependencies/runtime, exit state
   and actual reports. Zero tests, skipped tasks, cache hits and early prerequisites
   must remain visible. Do not count committed archived test XML as fresh output.
5. Create deduplicated new issues with archived original identities in their
   bodies. Preserve owner issue lifecycle/labels; stop on conflicting edits or
   ambiguous identifiers instead of silently replacing human work.
6. Only identity, preservation, attribution and verification-safety changes belong
   in the migration. Fixes and major architectural redesigns follow the prioritized
   roadmap with tests and separate design review. Publication/deployment requires
   separate explicit owner authorization.

## Consequences

The report may truthfully contain failed or unavailable platform checks and many
unresolved findings even when the migration is complete. That is preferable to
invented confidence. Reproducible isolated tests help narrow root causes but do not
replace lifecycle, concurrency, native ownership, accessibility or consumer tests.
Reports must follow the currently observed CI revisions rather than assuming an
older successful configuration certifies later workflow/build changes.

The independent archive preserves everything obtained through the documented
public observation, but unavailable/private/deleted metadata is explicitly outside
that guarantee. External dependency registries and platform SDKs remain build
prerequisites; “independent from Calf” does not mean a fully air-gapped toolchain.

## Rejected alternatives

- Calling all successful probes “unit tests” or presenting zero-test Cargo runs
  as native runtime coverage.
- Downgrading toolchains, replacing production native dependencies with silent
  stubs, or omitting failed prerequisites to obtain an apparently green audit.
- Promoting source risks to demonstrated vulnerabilities without preconditions.
- Reopening every historical issue or impersonating original GitHub users.
- Publishing a renamed release immediately because Git history was preserved.

## References

[Audit definitions](../audit/README.md), [verification ledger](../testing/README.md),
[metadata limitations](../migration/metadata-coverage.md),
[roadmap/release gates](../roadmap/README.md),
[identity decision](0001-independent-identity.md).
