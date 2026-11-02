# 0013 — Verify an owning JavaFX cancellation artifact before adopting it

**Date:** 2026-11-02. **Status:** accepted for private verification only.

## Problem and evidence

Original Windows #64/NATIVE-005 Stop acceptance still fails: the public Worker
is cancelled and NativeCmpKit reports Finished, but the held HTTP peer remains
connected. Exact OpenJFX21.0.13 `HTTP2Loader.fwkCancel()` only sets a callback
suppression flag. Cancelling its stored response future fixes four genuine
dependency-native cases on Linux and Windows. Those results are not library
acceptance; the historical Windows loader instance was not observed.

See [dependency evidence262–271](../development/evidence/current-platform-recovery-20261101/javafx-cancel262-271/README.md)
and [private artifact preparation273–282](../development/evidence/current-platform-recovery-20261101/javafx-full-candidate273-282/README.md).

## Decision

Build an explicitly identified **private** full `javafx.web` artifact from the
exact official platform JAR and source JAR, rather than editing a shared cache,
shadowing classes, disabling JavaFX's private HTTP2Loader route, or reflecting
into the current loader from NativeCmpKit.

`build_runtime_candidate.py` emits
`21.0.13-nativecmpkit-cancel1-local`. It replaces five existing loader class
members and the manifest. The four inner-class payloads are byte-identical to
upstream; only the top-level loader and manifest actually differ. Every other
payload, including public classes, JPMS descriptor and native libraries, is held.
The original header is retained, with a dated modification notice outside it.
The exact modification, original GPLv2/Classpath legal texts and Java source JAR
accompany the private candidate. Its manifest says publication-ready **false**.

An **explicitly loaded, one-task-only** Gradle init script removes the sole pinned
original web JAR from the test classpath and inserts the generated candidate
once, checking both digests. It does not affect normal builds or publications.
No runtime module patch, private loader property or public library API change
is allowed. A dedicated read-only Windows workflow runs only the failed original
public Stop method, retaining its original ten-second/six-predicate acceptance,
same-owner recovery and owned cleanup. Fresh XML, actual replacement marker,
daemon/runtime identity and held source/JAR maps are all required.

## Compatibility and limits

- Ordinary `org.openjfx:21.0.13` dependencies and all public NativeCmpKit API/package
  names remain unchanged. This is not a supported consumer installation option.
- Java sources are complete for this Java-source candidate, but **full upstream
  native corresponding-source/third-party obligations are not complete**.
  Preserved notices are not a redistribution or legal certification.
- Same-registry hash pins are consistency evidence, not independent provenance,
  signing, vulnerability or supply-chain clearance.
- Windows Stop1 success alone cannot close #64: remaining Desktop and genuine
  browser-offline original criteria still apply. Accepted unchanged populations
  are reused, not replayed.
- Workflow artifacts contain receipts/logs/XML only; no JARs, class files or
  source packages are uploaded. No package, deployment or release is authorized
  by this decision. Existing release-readiness/security gates remain.

## Before any ordinary adoption

1. Review actual original library Stop1 source/results/runtime/cleanup evidence.
2. Prefer a verified upstream fix if available; otherwise define a maintained,
   independent dependency artifact and ownership/update policy.
3. Complete corresponding-source, licensing/notices, independent provenance,
   dependency/advisory and native-binary security review.
4. Verify all supported Desktop classifiers and packaged consumers, module and
   public API/ABI behavior, native loading and cancellation/resource lifetimes.
5. Document installation/versioning changes and finish all release prerequisites.

The project continues solo, with serial local heavy work, an 8GiB disk reserve
and at most two combined hosted-heavy reservations including queued jobs.
Actions allow all actions without mandatory SHA pinning; voluntary reuse of an
existing verified revision does not create a mandatory policy.
