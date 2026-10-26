# Dependency integrity: bootstrap evidence and remaining gates

This is additive BUILD-007 development evidence, **not a resolution/closure** of
the baseline supply-chain finding. Acquisition from the same registry that serves
an artifact supplies consistency checks, not independently trusted provenance.
Current [containment](containment.md) authorizes routine dependency acquisition
and verification workflows without further approval. Publication and deployment
remain gated; this authority does not waive trust or actual-runtime prerequisites.

## Verified documentation scope

See [`requirements/README.md`](../../requirements/README.md). A fresh, isolated
Linux x64 CPython3.12 environment installed 41 unique exact artifacts (38 runtime
packages plus four backend tools, with one overlap). SHA256 was checked before
pip, pip required hashes and used the local wheelhouse without index/cache/build
isolation, installed versions matched exactly, and `pip check` exited 0. A
separate local Babel fixture with an all-zero expected checksum produced pip's
specific hash-mismatch error and exit 1 with the real observed digest. This is an
actual negative test, not an unrelated network failure or mocked return value.

- `evidence/build/docs-locked-001-receipt.json`: package/install/hash checks passed;
  strict MkDocs failed on one stale relative baseline `CupertinoSlider.kt` link.
- The link now addresses the preserved destination repository's immutable
  `af388bd...` source, without changing audit claims. `development/evidence/**`
  is excluded from site rendering/search; raw public archive material remains in Git.
- `evidence/build/docs-locked-002-receipt.json`: second fresh install, exact graph,
  `pip check`, actual wrong-hash rejection and strict local MkDocs all passed,
  elapsed65.74s; locks unchanged. MkDocs itself completed in5.18s. **No deployment.**
- `evidence/build/docs-lock-self-tests.log`: nine offline parser/integrity fixtures,
  covering unpinned/duplicate input, foreign origins, graph mismatch, changed lock,
  symlinks, wrong bytes and false trust claims; not native/library test executions.

The two sdist-only minifiers execute their checked source via a pinned backend;
this is not independent code review or a network sandbox. Generated wheels are
not claimed bitwise reproducible. Other Python/OS scopes need their own acquired
and tested locks. Active workflows have not been changed to install these locks.

## JS/Wasm: project locks bootstrapped, ordinary enforcement unverified

The actually installed KGP2.4.20 APIs were inspected via `javap`. Root typed
configuration compiled successfully with the exact inspected default versions
Node24.16.0 and Yarn1.22.22, separately for JS and Wasm environments. Both use
`ignoreScripts=true`, lock mismatch **FAIL**, `yarnLockAutoReplace=false`, and
`reportNewYarnLock=true`. `kotlin-js-store` is no longer ignored by Git.

**Both project Yarn lockfiles now exist; ordinary frozen-install enforcement is
not established.** Separate actual browser results are described below; they do
not retroactively turn lock acquisition into independent trust.
KGP's store/mismatch policy is not by itself proof that Yarn ran with a
package-manager-level frozen-lock option. That distinction needs verification
after materialization; lifecycle-script suppression also needs real browser tests.

| Command scope | Inspected result |
|---|---|
| Bounded `./gradlew tasks --all` | Exit0,14.01s; root typed environment configuration compiled and actual upgrade task names discovered |
| `kotlinUpgradeYarnLock kotlinWasmUpgradeYarnLock` | Exit1,14s; Maven resolution failed with Java TLS handshake termination before install; no locks |
| Same tasks plus `--no-daemon`, after fresh-JVM HTTPS observations | Entered actual `kotlinNpmInstall`, generated JS/Wasm package JSONs and set up Node/Yarn, then hit300s bound; exit143/300.42s; no locks |
| Third explicit bootstrap, both upgrade tasks and `--no-daemon`, bounded600s | Exit0/122.03s; JS/Wasm stored locks byte-match generated locks;701 preexisting selected inputs unchanged plus exactly2 new locks; **zero tests** |

The first two materialization attempts captured selected build/settings/convention/catalog/
wrapper inputs before/after. Their selected bytes remained unchanged; the second
also preserved conditional Android-test-directory topology. Library/test owners
could edit ordinary source during acquisition, so neither receipt claims an
immutable full source tree or source compilation. Fresh JDK17/21 HTTPS success for
one exact POM does not prove the first daemon caused the transport failure.

Evidence: `evidence/build/yarn-materialization*-verification.json`, corresponding
logs/results, and `yarn-transport-observation.json`. Original failures are retained.
No TLS verification, certificates or protocol security were disabled.

The third [bootstrap receipt](evidence/build/yarn-materialization-003.summary.json)
binds135 files, including124 generated root/workspace manifests. Both Yarn
processes used `--force --ignore-scripts --network-concurrency 1 --mutex network`;
these were explicit bootstrap invocations, **not frozen ordinary installs**.
The JS lock records439 resolutions:438 registry tarballs with acquired SHA512 SRI,
plus `github:Kotlin/karma#6.4.5`, package version6.4.4, pinned to commit
`239a8fc984584f0d96b1dd750e7a5e2c79da93a6` at the exact codeload endpoint and
**no integrity entry**. Do not call all439 SRI-verified: the VCS tarball's byte
integrity and independent provenance remain uncovered. The Wasm project lock has
2/2 SRI entries, but its separate embedded-lock tooling setup was not part of
this bootstrap; the later diagnostic is recorded below. The
collector's initial origin rejection is preserved additively; no browser, native,
consumer, vulnerability-clearance or release result is implied.

Separately, [actual full-requested JS003](evidence/js-full-003/archive.json)
passed286/286 cases across19 modules/48 XML reports, exit0/70.02s, with691 selected
inputs unchanged. Earlier full/focused JS failures remain preserved. This proves
that scoped Chrome/library execution, not package-manager-level frozen graph
enforcement, complete VCS SRI/tooling coverage, Wasm execution or release trust.

The subsequent [cold Wasm-tooling001 diagnostic](evidence/wasm-tooling-001/archive.json)
ran `:kotlinWasmToolingSetup` once with a fresh task-owned `kotlin.user.home`:
exit0/94.94s,691 selected inputs unchanged,13 archive hash bindings, **zero tests**.
The retained Gradle process-launch log records the exact Node/Yarn argv and
tooling cwd with `--ignore-scripts` and **no `--frozen-lockfile`**; this is not
external OS process instrumentation or a package script-marker test. The actual
tooling lock byte-matches KGP2.4.20's embedded resource and has489 lexical resolver
entries/488 integrity entries, plus the same exact-commit Karma VCS entry without
SRI. Those lexical counts are not parser/closure validation. This separate graph
is not the two-entry Wasm project lock. Shared Gradle/Yarn/host caches were not
isolated; warm-skip/tamper/closure, independent provenance and browser/runtime
gates are not passed by this install. Earlier proposal and bootstrap records
remain unchanged.

## Gradle: isolated tooling and actual local-Maven fixtures

[`scripts/dependencies/`](../../scripts/dependencies/README.md) is implemented
without installing policy into ordinary root/convention builds. It copies current
dirty source/topology into an external marked workspace, records per-owner graphs,
uses strict actual-host project locks and checksum verification, and refuses
partial/unresolved acquisition or conflicting artifact hashes. Buildscript,
settings/plugin and detached **version-lock** gaps stay explicit. Its164 core006 offline
tests are parser/orchestration checks, not Gradle/runtime passes.

- Fixture001: actual Gradle9.7.1/JDK17.0.20 init execution failed closed on an
  unhandled synthetic script root. XML existed despite failed acquisition and
  no finalized project lock. No positive/negative checks ran.
- Fixture002: after explicit public-root modeling, bootstrap and ordinary baseline
  passed; altered JAR bytes produced the exact expected/actual SHA256 and real
  verification exception. Strict transitive drift also failed in Gradle, but the
  first observer missed its precise `from lock file` wording; suite exit1 is kept.
- The narrow repaired observer matches the exact three leaf edges, typed conflict,
  old lock and both versions' known JAR/POM hashes. Read-only structured analysis
  of002 confirms that conflict without rewriting historical results. Fresh003
  then passed exactly bootstrap/baseline/transitive rejection in25.722s; its
  selected-subset flag is true and its all-cases flag remains false.
- Independent review reproduced a generic lock-message false positive in four
  then-unexecuted cases. The corrected matcher requires exact typed/configuration-bound
  errors, known fixture state and the exact missing/stale lock discrepancy, with
  no unrelated failure. Its positive shapes were initially synthetic/offline only;
  actual004 later reached missing-host-lock but retained an unverified classifier
  verdict; the other three cases never ran. `checkpoint-offline-004.json` records
  the146-test repair;001/002/003 evidence and the115-test003 baseline are preserved.
- Separate frozen005 records157 offline tests, exit0/2.339s. It generates exact
  private JVM home/temp/Gradle/Kotlin-daemon properties and private HOME/Gradle/
  KONAN/XDG/temp environment paths instead of assuming HOME changes Java's
  `user.home`. Inherited JVM/cache overrides, unsafe option paths and symlinks
  are rejected. Two bounded direct JDK17 source-launcher probes (plain and spaced
  candidate paths) each checked15 selected values successfully. These are **not
  Gradle client/daemon, Kotlin/Native or actual compiler-cache-use observations**.
  Actual004 subsequently compiled/executed the init guards and wrote three scoped
  actual Gradle-JVM/runtime receipts.005 also records the owned launched PID,
  explicitly not a Java identity. Full client/daemon runtime bindings are still
  required before any real-source acquisition. The generated paths are not an
  OS filesystem sandbox; explicitly selected SDKs remain external.
- The additional [passive witness](../../scripts/dependencies/runtime-witness.md)
  first had a separately frozen002 correction with successful independent offline
  re-review.001's76
  offline tests passed, but independent mocked argv replay found that a later
  Gradle-looking suffix did not prove the actual JVM entrypoint/effective
  classpath. No unrelated JVM was attached.002 requires the complete installed
  client vector and a fully consumed bounded daemon-option/entrypoint grammar.
  Its91 tests passed in0.176s; unchanged157-test core regressions passed in2.367s.
  Independent re-review reran91 tests and checked14 synthetic identity scenarios
  plus11 modeled outer-loop outcomes; it did not execute the actual producer.
  These tests use synthetic `/proc`/jcmd data and tiny owned Python pipe fixtures;
  **no Java, jcmd or Gradle ran in the tests**. Read-only `javap`/installed-script
  inspection supports the grammar, not actual runtime proof.
- The exact paired fixture004/witness002 command ran once after explicit review
  and scheduling: suite exit1/26.715s; witness exit1/26.756s. Bootstrap and strict
  baseline passed; missing-host-lock returned Gradle1 and the actual exact
  `MissingLockStateException` message, but005's classifier rejected the preceding
  `TypedResolveException` wrapper. The original negative verdict remains
  **unverified**; three later selected negatives did not execute. All three005
  runtime receipts match the frozen selected Gradle-JVM/environment paths, and
  external `jcmd` observations matched all three installed-distribution clients.
  **Zero daemon diagnostics were attempted; no daemon identity/runtime binding
  was established.** Candidate-specific validation errors were discarded by002,
  leaving only `required-observation-input-unavailable`; its actual cause is
  unknown, not an assumed ancestry/argv defect. There was no invocation timeout,
  interruption or disk stop. All six recorded client/Gradle-JVM PIDs were absent
  at the completion check; no signals were sent. That slot was released. Narrow
  offline corrections followed below, not another fixture or source run.
- [Core006](evidence/build/dependency-fixtures/checkpoint006/archive-manifest.json)
  passed164 offline tests in2.637s and independent source/offline review. It adds
  only the actual `TypedResolveException`/dependencies message pair, retaining
  unrelated-cause, exact configuration/state and missing-host requirements. Pure
  Python classfile inspection confirms the pinned Gradle hierarchy/format.
  [Read-only reclassification](evidence/build/dependency-fixtures/fixture004-missing-host-reclassification-006.json)
  of retained004 now matches the exact missing-host rejection. This does not
  rewrite the failed original suite or execute006 against Gradle; its driver,
  model and init files remain005 bytes, and the other three negatives never ran.
- [Observer003](evidence/build/dependency-fixtures/runtime-witness003/archive-manifest.json)
  passed108 offline tests in0.288s, plus164 unchanged core006 regression tests
  in2.807s. Its separate [independent source/offline review](evidence/review/dependency-observer003-independent.md)
  is GREEN:108 tests rerun in0.273s,17 additional modeled outer-loop checks and
  bounded enum/poison/saturation checks passed. This is not actual runtime proof.
  It retains bounded
  enum-only rejection counts (six stages/85 codes,1024 cap per stage/code), without
  raw exception/argv/property/environment bodies or new process ownership.
  Twenty-six prior function/class ASTs, including all ownership/entrypoint/pidfd/capture
  and completion gates, are unchanged; failed diagnostics are not retried.
  Nine modeled outer-loop tests are not actual runtime observations or a diagnosis
  of004's discarded errors. Counters are not a complete event log: absent
  launch/runtime files or false runtime equality can remain uncounted; saturation
  loses exact counts and ordering. Empty counters do not prove no guard failed.
  Fixture005/root acquisition were not authorized at that checkpoint. The
  2026-10-26 owner decision now permits routine verification; actual runtime,
  source-freeze and SDK-write safeguards still apply. Historical checkpoint flags
  and sealed prior reviews remain unchanged, not retroactively successful.

The [persistent fixture archive](evidence/build/dependency-fixtures/README.md)
contains exact invocation/owner/configuration receipts, input/tool bindings,
XML/locks and sanitized logs. It excludes caches/binaries/private context. This
is controlled-fixture evidence, not real library dependency acquisition,
independent artifact trust or release readiness.
The additive [003 verification](evidence/build/dependency-fixtures/fixture003/archive-verification.json)
binds60 files/53 original pairs. Source snapshots now include `kotlin-js-store`
as immutable inputs; this is not Yarn enforcement or coverage of KGP's separate
Wasm tooling installation. See [the read-only Yarn policy review](evidence/build/yarn-frozen-policy-review.md).
The independently scoped [004](evidence/build/dependency-fixtures/checkpoint004/archive-manifest.json)
and [005](evidence/build/dependency-fixtures/checkpoint005/archive-manifest.json)
archives bind the exact tooling and logged tests;005 additionally binds its
[direct JDK17 probe](evidence/build/dependency-fixtures/checkpoint005/direct-jdk17-runtime-path-probe.json).
The additive [witness001 archive](evidence/build/dependency-fixtures/runtime-witness001/archive-manifest.json)
and [witness002 archive](evidence/build/dependency-fixtures/runtime-witness002/archive-manifest.json)
do not replace either core checkpoint or hide the reviewed001 defect.
The additive [actual004 archive](evidence/build/dependency-fixtures/fixture004/archive-verification.json)
binds73 files:66 exact/sanitized-original pairs plus six derived XML/JAR-hash
records and the manifest. It preserves the failed suite/witness receipts, all
three launch/runtime receipts, nine exact tool inputs and preflight/completion
evidence. Neither its historical005 checkpoint nor its original004 results are
rewritten after later analysis. The concrete, still-unscheduled current-source
snapshot/root/standalone-convention proposal and its SDK/resource limitations are
in [the implementation plan](build007-implementation-plan.md#current-source-acquisition-proposal-not-scheduled-or-executed).

## Concrete next acquisition/enforcement sequence

Coordinate a fresh bounded build slot with the lead; do not run these in parallel
with compiler/native/consumer verification or automatically overwrite locks.

The additive [BUILD-007 implementation plan](build007-implementation-plan.md)
defines the minimum root/composite and standalone-convention scope, per-configuration
receipts, actual-host locking, candidate review, conflict-rejecting trust import and
specific negative tests. The isolated helper/partial-fixture status is described
above; root/convention acquisition and ordinary-build enforcement remain future
gates. Read-only Gradle9.7.1 bytecode evidence and actual failed fixture001 explain
why emitted verification metadata alone cannot establish complete acquisition.

1. **Preserve/review explicit JS/Wasm bootstrap.** The third invocation of
   `kotlinUpgradeYarnLock kotlinWasmUpgradeYarnLock`, in a larger bounded,
   source-configuration-stable window, produced both project locks. These are explicitly mutating bootstrap
   tasks, not ordinary frozen installation. Preserve generated package manifests,
   dependency versions, stored locks and runtime versions with hashes and scope.
   Stop/record any unresolved graph rather than copying another version's lock.
2. **Prove JS/Wasm enforcement.** Run ordinary actual install/store tasks against
   the checked-in locks, confirm exact Node/Yarn versions and suppressed scripts,
   inspect KGP's install-argument API before adding a package-manager frozen-lock
   argument, and prove missing/drifted/integrity-mismatched lock rejection in
   isolated project-owned fixtures. Do not corrupt shared Node/Yarn caches or
   silently use upgrade tasks in normal tests/CI. Execute real JS/Wasm tests
   against the enforced policy; earlier JS003 and tooling001 results do not prove
   that future policy.
3. **Acquire Gradle graphs, root and convention build separately.** A dedicated
   source-free graph acquisition task should enumerate all resolvable
   configurations, record configuration attributes, actual selected external
   components/artifacts and every failure, and fail if any required configuration
   remains unresolved. Project components must not accidentally trigger library
   compilation in a dependency-only slot. Explicitly include convention plugin
   compile/runtime/plugin dependencies and root target/test/tool configurations;
   do not claim ordinary `dependencies` output resolves all actual artifacts.
4. **Bootstrap SHA256 verification and version locks.** Use actual Gradle9.7.1
   `--write-verification-metadata sha256 --write-locks` while acquiring the
   enumerated graphs. Review metadata/POM/module checks as well as artifacts;
   require metadata verification, avoid broad trusted-artifact exceptions, and
   do not invent trusted signing keys. Mark all acquired checksums **TOFU** until
   an independent trust process is performed. Locking must also be active on
   ordinary root/convention builds, not only an optional acquisition invocation.
5. **Do not hide incomplete target graphs.** Linux may acquire Apple KLIB
   dependencies but cannot prove Apple SDK/cinterop/runtime compatibility; the
   WebView Apple cinterop is actually disabled here. Record disabled/unresolved
   configurations and complete relevant graphs on capable hosts before strict
   cross-host completeness claims. Conditional instrumentation configurations also
   require explicit coverage now that device test source sets exist.
6. **Test rejection before calling enforcement complete.** In small isolated
   repository/cache fixtures, establish a known-good artifact/metadata graph,
   corrupt an artifact and separately metadata, remove an expected hash and
   change a locked version, then inspect each precise Gradle rejection. Never
   mutate the shared Gradle cache or infer a security pass from any nonzero exit.
   Rerun complete target graph verification after intentional updates and bind
   caches to verified manifests/toolchains/runtime, not broad restore prefixes.
7. **Scan the acquired graph, not the catalog alone.** Record all exact resolved
   Kotlin/Java/npm/native distributions, query current advisories with ecosystem
   semantics, and review native/embedded engine code and license obligations
   separately. The existing exact JavaFX-coordinate queries are scoped observations,
   not whole-library clearance.

Ordinary root/convention verification metadata and owner-lock policy are **not
installed**; controlled fixture candidates are not production trust. Rust
locks/native-license collection and immutable ABI/consumer verification are owned
by their existing source/consumer reviewers; incomplete legal material is a
publication blocker, not something checksum generation fixes.
