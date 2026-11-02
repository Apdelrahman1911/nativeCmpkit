# 0013 — Verify an owning JavaFX cancellation artifact before adopting it

**Date:** 2026-11-02. **Status:** accepted for private verification only.

## Problem and evidence

The historical original Windows #64/NATIVE-005 Stop acceptance failed: the public
Worker cancelled and NativeCmpKit reported Finished, but the held HTTP peer
remained connected. The private Windows full-JAR candidate now passes the original
library Stop method; ordinary dependencies are unchanged. Linux ARM64 and both
macOS original Stops failed at that checkpoint with the same precleanup scalar
observations. Later candidate originals now accept all three missing hosts:
[macOS ARM64](../development/evidence/current-platform-recovery-20261101/javafx-native-egl363-372/README.md),
[macOS x64](../development/evidence/current-platform-recovery-20261101/javafx-macos-x64-native374-377/README.md)
and [corrected Linux ARM64](../development/evidence/current-platform-recovery-20261101/javafx-linux-native373-380/README.md).
The Linux EGL prerequisite is fixed; automatic GL fallback still is not GPU/
painted-content certification. Ordinary dependency adoption remains incomplete.
Exact OpenJFX21.0.13 `HTTP2Loader.fwkCancel()` only sets a callback
suppression flag. Cancelling its stored response future fixes four genuine
dependency-native cases on Linux and Windows. Those results are not library
acceptance; the historical Windows loader instance was not observed.

See [dependency evidence262–271](../development/evidence/current-platform-recovery-20261101/javafx-cancel262-271/README.md)
and [private artifact preparation273–282](../development/evidence/current-platform-recovery-20261101/javafx-full-candidate273-282/README.md).
The [Windows library result](../development/evidence/current-platform-recovery-20261101/platform-originals308-315/README.md),
[Linux originals](../development/evidence/current-platform-recovery-20261101/desktop-linux-native346-349/README.md)
and [macOS originals](../development/evidence/current-platform-recovery-20261101/desktop-macos-native350-354/README.md)
separate accepted methods from the three still-failed Stops.

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
is allowed. The dedicated read-only workflow selects **one actual host** per
dispatch: Linux ARM64, macOS ARM64 or macOS x64. Windows remains an explicit
compatibility option, not an instruction to replay its accepted result. Each run
selects only the failed original public Stop method, retaining ten-second/six-predicate acceptance,
same-owner recovery and owned cleanup. Fresh XML, actual replacement marker,
daemon/runtime identity and held source/JAR maps are all required.

Native jobs in **both** JavaFX workflows are now **manual-only**. Historical
development push registration events remain, but adding platform pins or changing
candidate tooling must not automatically replay accepted Windows/Linux methods.
Each candidate dispatch reserves one hosted-heavy slot; the project-wide limit
is two, including queued/reserved jobs. Cache identities remain OS/architecture/
slot/dependency/runtime-bound; cache only dependencies, not test success.

The fixed official21.0.13 pins include Linux ARM64 and both macOS classifiers.
`--target-classifier` in the builder permits **packaging only**, recording the
actual compiler host and zero native executions. The library runner and Gradle
init script independently require the classifier to match the actual native host
and daemon; a cross-packaged JAR is not platform functionality evidence.

## Compatibility and limits

- Ordinary `org.openjfx:21.0.13` dependencies and all public NativeCmpKit API/package
  names remain unchanged. This is not a supported consumer installation option.
- Java sources are complete for this Java-source candidate, but **full upstream
  native corresponding-source/third-party obligations are not complete**.
  Preserved notices are not a redistribution or legal certification.
- Same-registry hash pins are consistency evidence, not independent provenance,
  signing, vulnerability or supply-chain clearance.
- Windows Stop1 success alone did not close #64. The three later missing Desktop
  Stops now pass, but ordinary dependency adoption still applies. The browser offline-destination
  subset is now accepted, not system-offline/DNS/TLS certification. Accepted
  unchanged populations are reused, not replayed.
- Workflow artifacts contain receipts/logs/XML only; no JARs, class files or
  source packages are uploaded. No package, deployment or release is authorized
  by this decision. Existing release-readiness/security gates remain.

## Current upstream fix check — 2026-11-02

[Read-only observation386](../development/evidence/current-platform-recovery-20261101/javafx-upstream-cancel-observation386/README.md)
finds `jfx21u/master` at `dd5bd597dc166a8b3807cde608109d0b6dc156be` still uses
the same flag-only `HTTP2Loader.fwkCancel()` source as official21.0.13. The
24,544-byte Java source SHA256 is identical; the latest path change dates2022.
Do not assume a later21u branch/version fixes cancellation. This is not official
native-binary correspondence, a verified new release, or legal/security clearance.
No code/dependency/candidate change or native/build execution follows. The first
private-selector parser refusal and same-byte recovery are retained.

## Before any ordinary adoption

1. Review actual original library Stop source/results/runtime/cleanup evidence
   on all missing hosts, preserving prior failures and accepted subsets.
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
