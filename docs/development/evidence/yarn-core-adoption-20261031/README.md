# Corrected inert Yarn-core source-review archive — 2026-10-31

This compact archive preserves **owned source/evidence only**, not an installed
ordinary root policy. The exact corrected three-new-file patch is
`inert-core-snapshot-and-synthetic-tests.patch` (SHA256
`d1520d201abc59ab117f46a17bc42069841ffb573087f473dfb87cdc6e14ee6e`).
It contains the inert Kotlin core, synthetic repository fixture and developer doc.
No third-party source/binary, generated package JSON/lock, raw private fixture,
host cache or private machine path is archived. Standard JDK installation examples
inside the exact owned-code patch are retained; they are not cached dependency paths.

## Owning defect and repair

The prior inert core's `CheckedGraph` constructor/getter exposed a multi-element
Kotlin `toList()` backing list. Source and exact previously compiled bytecode show
that it can be writable on the JVM: removing/replacing receipts weakens recheck
and working-lock expectations. An unmodifiable view alone retains a constructor
alias. The corrected constructor defensively copies and JDK-unmodifiable-wraps
trusted receipts while preserving the public getter/type and other executable
parser/traversal bytes. See `owning-receipt-snapshot.delta.patch`.

The new snapshot regression covers remove/set/clear/iterator mutation refusals,
constructor-alias isolation and preserved workspace drift refusals at both
boundaries. Source guard red/green is retained, **not runtime red/green**.

## Evidence and reuse, without recounting

- `delivery-readback.json` reuses the final **105 private file/hash/source checks**,
  exact three-file reconstruction,13 selected preimages and28 original evidence
  bindings. Archive preparation did not rerun those checks or models.
- `initial-readback-refusal.json` retains the initial owning schema-selection
  refusal: three selected plan/result/XML entries omitted separately bound source,
  class and log fields. Recovery merged those fields without lowering the binding
  minimum or weakening hashes. This was not a core/compiler failure.
- Original private33 model/10.4453s typing receipts stay at their original scope.
  **31 inert-v1 method bodies are preserved;29 are unchanged original synthetic
  bodies.** These numbers are not newly accepted executions.
- Corrected repository fixture:32 authored methods. The lead's finite request
  selects **two changed filesystem methods plus one new snapshot regression**.
  No actual three-method results have been received in this source-review archive;
  inspect their later fresh XML separately, including every failure/skip.

`input-bindings.json` uses repository-relative/logical identities and original
hashes; historical bytes are not claimed to be physically present here. Public log
copies remove only private traceback prefixes and record both original and copied
hashes. The source guard is review evidence, not a production Python bridge.

## Unchanged holds

Exclusive trusted ownership and stable root/ancestor identities remain caller
preconditions, not an implemented hostile-filesystem gate. NIO remains **non-atomic**;
a substituted FIFO can block despite a byte cap. Concurrent writers, Windows
reparse/junction, macOS/other host behavior remain unverified; symlink capability
skips are not host acceptance. This snapshot repair does not fix those gaps.

Actual JS aliases/Git and separate Wasm tooling remain held. Declared selector,
registry URL/SHA512 syntax is not fetched-byte, semver, provenance, advisories or
complete metadata trust. Mandatory closure-before-restore and actual cold/warm/
direct/bootstrap task ordering/provider binding/child argv remain unverified.
Unknown primary tasks must be refused; do not import the old early-return or
restore-first adapter. **#40/BUILD-007 remains open**. No root hook, issue closure,
publishing/Pages/main/history, native/minimum/consumer/API-ABI/legal/dependency/
security/release-readiness waiver is implied. Serial local builds,8GiB reserve
and max-two combined heavy requests remain required.
