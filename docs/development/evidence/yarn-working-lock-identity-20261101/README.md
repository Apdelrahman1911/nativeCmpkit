# Working-lock identity repair — 2026-11-01

The inert `CheckedGraph.requireWorkingLock` accepted the stored lock itself or
a hard link when its bytes matched, even if the separate working lock was absent.
The reader already validated file identities but discarded them. It now retains
that private identity, freshly binds the stored receipt, and refuses an alias
before the existing byte/hash comparison. Public receipt shapes and the other
reader/parser/refusal contracts are unchanged.

## Actual important verification

- [Original-core red](jvm-red002/RECEIPT.json): two new JVM methods, both fail
  the expected alias rejection; fresh original XML, Gradle1/23.01s.
- [Repaired-core green](jvm-green001/RECEIPT.json): the same two methods pass,
  zero skips/errors, fresh original XML, Gradle0/28.01s. The actual standalone
  convention daemon reports JDK17/Gradle9.7.1.
- Both commands are offline, serial, one worker, no build-cache reuse, with an
  8GiB reserve and held source maps. The hard-link setup and owned fixture
  removal execute; an independent equal-byte replacement remains accepted.
- All32 previous method bodies are preserved and unselected. The sealed five
  source/mock outcomes are reused, not rerun or counted as native verification.

[jvm-red001](jvm-red001/CALLER-FAILURE.json) preserves the lead's earlier
incorrect init-script path: zero test/XML execution, not the expected defect red.
The original root-only JVM observer does not observe the standalone convention
daemon; the green uses a separately bound, convention-only observation script.
The [proposal](proposal001/LEAD-DELIVERY-VERIFICATION.json) also preserves the
importer's exact public-phrase privacy false positive; no private path was added.

**#40 remains open.** The utility remains unwired into ordinary builds. This
repairs a real prerequisite, not frozen installation, artifact trust, concurrent
path-swap atomicity, Windows reparse safety, U1–U3, network/RSS containment,
ordinary dependency enforcement, release readiness or publishing authorization.
