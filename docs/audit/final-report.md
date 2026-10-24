# nativeCmpkit migration and technical audit report

**Report baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`, reviewed on
2026-10-24 UTC. **Destination:**
[Apdelrahman1911/nativeCmpkit](https://github.com/Apdelrahman1911/nativeCmpkit).

Git recovery, metadata archival, implementation review and issue delivery are
verified separately below. This is a **migration/audit delivery report**, not an
all-platform-pass or production-readiness certificate. One administrative cleanup
remains unresolved: unpublishing the unintended legacy Pages deployment, tracked
in [issue #171](https://github.com/Apdelrahman1911/nativeCmpkit/issues/171).

## Executive assessment

nativeCmpkit is an independently maintained copy of a substantial KMP native
integration library. It contains useful reusable APIs and working source-tested
logic, but **is not ready for an unqualified production release**. Many targets
share API shapes without equivalent capabilities; several native ownership,
file-safety, permission, accessibility and build-distribution paths have concrete
defects. “Compiles on a target” and “works correctly on that target” are materially
different claims here.

The audit documents **164 findings: 0 Critical, 37 High, 106 Medium and 21 Low**.
Evidence classes: **105 source-confirmed, 23 scoped test-confirmed, 24 risks and
12 improvements**. These are not 164 security vulnerabilities. Three baseline
build findings are migration-resolved, while functional changes are left for
reviewed follow-up rather than bundled into an uncontrolled migration rewrite.

## Deliverables

| Requested result | Delivered record |
|---|---|
| Independent repository and retained identity history | Destination non-fork repository; all 46 original branches/23 tags; original main is an ancestor of additive migration commits |
| GitHub history and offline recovery | [Migration/recovery guide](../migration/README.md), [metadata coverage](../migration/metadata-coverage.md), original and supplemental bundles, raw metadata and checksums |
| New library identity and attribution | [Identity map](../migration/identity.json), [modifications](../migration/MODIFICATIONS.md), LICENSE/NOTICE/third-party provenance, compatible public namespaces |
| Implementation-level audit | [Audit overview](README.md), [all findings](findings-index.md), subsystem reports, [source inventory](source-inventory.json) |
| Persistent project knowledge | [Architecture](../architecture/README.md), [modules](../modules/README.md), [platforms](../platforms/README.md), [decisions](../decisions/README.md), [AGENTS.md](../../AGENTS.md) |
| Tests and build investigation | [Exact execution ledger](../testing/README.md), original tests, scoped probes, CI logs, toolchain/dependency evidence |
| Organized work | [170 verified managed issues](../migration/issues-verification.json), [issue map](../migration/issue-map.json), original-topic dispositions, [complete prioritized roadmap](../roadmap/README.md), and separate operational Pages issue #171 |

The reviewed inventory contains **607 baseline files, 479 source files and 43,653
Kotlin/KTS/Rust lines**. Area ledgers document actual implementations, ownership,
callbacks and error paths; the lexical inventory alone is not proof of semantic
correctness. All 24 included library Gradle projects, 21 publication-enabled
projects, platform sample shells and excluded experiments are mapped. Generated
symbol/font data is validated as data rather than counted as thousands of
independently reasoned algorithms. All **424 finding citations** were validated
against preserved baseline objects.

The issue snapshot is **171 total: 168 open, three closed**. Of these, **170** are
managed audit/history issues: 164 findings plus six independent actionable
historical topics (167 open, three closed). Every managed marker, body hash,
number, label, author, creation time and recorded state was independently checked.
The one additional Medium operational issue is deliberately not treated as a
baseline library defect or folded into that issue map. All 17 original open-item
dispositions and historical references are retained.

No release or package was published. One **unintended legacy Pages deployment**
was recorded from the imported historical branch. Legacy publishing is disabled,
but the existing deployment could not be removed through the API; the owner was
asked to use GitHub's **Unpublish site** control without deleting the branch.
See [the incident record](../migration/pages-incident.md); no successful
unpublishing is assumed. The new coordinates are
prospective, not installable published artifacts. Historical Calf tags/releases
are archives, not endorsed nativeCmpkit releases. No upstream GitHub setting,
issue, PR or Git history was modified.

## Highest-impact findings

| Area | Concrete concern | Recommended first action |
|---|---|---|
| IO | IO-001 oversized iOS native copy; IO-004 desktop self-save deletion; IO-002 Android pending-content loss | Define bounded reads and safe source/destination semantics; add failing boundary/recomposition tests before fixes |
| Native ownership | IO-003 raw JNI handle/disposal races; NATIVE-002 retained engines; UI-018 incomplete presentation teardown | Introduce explicit ownership/state transitions without broad API rewrites; instrument cancellation/disposal/late callbacks |
| Permissions | PERM-002 alias result assignment; PERM-008 concurrent incomplete batches; PERM-009 missing Always upgrade; PERM-011 iOS version gating | Test identity/prerequisites, sequence native requests, guarantee complete exactly-once results and API availability checks |
| UI | Native calendar interpretation, stale alert callbacks, iPad popover presentation, permanent bar-measurement stop, gesture/accessibility gaps | Platform fixtures across calendars/locales/iPad/rotation and real accessibility/pointer interaction |
| WebView/share | NATIVE-001 stop command re-enqueues; NATIVE-013 global cookie-handler overwrite; conditional isolation/arbitrary-opening risks | Separate commands from events, preserve cookie ownership, make trust/capability policies explicit |
| Navigation/geo | Dropped arguments and duplicate-route saved state; public location state never updated | Focused duplicate-entry and state/error propagation regressions; do not advertise unfinished modules as supported |
| Build/distribution | BUILD-001 publisher-host JavaFX classifiers; BUILD-003 incomplete native prebuilt detection | Consumer fixtures on every promised host/architecture and per-module native provenance/content manifests |

The [finding records](findings/) contain exact code locations, roots, impact,
recommendations, compatibility risks and required tests for **every** item.
Priorities and dependency ordering are in the [roadmap](../roadmap/backlog.md).

## Verification actually established

### Executed builds and tests

| Check | Inspected result and scope |
|---|---|
| Full existing desktop test inventory through real Gradle/Compose | **86 tests passed**, zero failures/errors/skips, 13 XML reports: IO 6, picker 9, UI 69, navigation 2. The final local invocation used `--rerun-tasks`; all 55 actionable tasks executed, exit 0, 311 seconds. [Command receipt](../testing/evidence/migrated-real-desktop-tests.log.result.json), [independent XML counts](../testing/evidence/migrated-real-desktop-summary.json). No platform stubs. |
| First Gradle CI, `3d2b772b27bed3da0f34677225b843d29f1c3ba6` | [Run 40110188721](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40110188721) **failed overall**, but actually executed **32 JS + 32 Wasm tests**, zero failures/errors/skips, 8 XML reports. JS sample distribution completed with four webpack warnings. Wasm production compilation exhausted a 2 GiB heap. Invalid SDK package spelling caused desktop/Android/Apple steps to be skipped; macOS executed zero tests. [Inspected receipt](../testing/evidence/github-actions/gradle-verification-summary-40110188721.json). |
| Corrected Linux Gradle CI, `1160893ca17404891b312990bc829535cddb75a2` | [Run 40114966617](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40114966617): **182 fresh test executions passed** — 86 desktop, 32 Android-host, 32 JS and 32 Wasm; zero failures/errors/skips, 25 XML reports. All seven populated test task invocations executed rather than restoring cached test results. Android `assembleDebug` and both browser production distributions succeeded. JS production compilation/webpack reused prior cached outputs; Wasm production compilation, optimization, webpack and distribution executed freshly. [Independent XML counts](../testing/evidence/github-actions/gradle-junit-linux-40114966617.json). |
| Corrected macOS/Apple Gradle CI, same revision/run | **118 fresh test executions passed** — 86 desktop and 32 iOS Arm64 simulator common tests; zero failures/errors/skips, 17 XML reports. All five populated test task invocations executed freshly. The sample's `linkDebugFrameworkIosSimulatorArm64` succeeded, with 713/713 actionable Gradle tasks executed in 22 minutes 24 seconds. [Independent XML counts](../testing/evidence/github-actions/gradle-junit-macos-40114966617.json). This is not a signed Xcode application or physical-device/native-UI test pass. |
| Host Rust compilation, `cf6547931d8e339d673e7605ff5fd141a5e42091` | [Run 40106895492](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/40106895492) compiled both crates on Windows, macOS and Linux. **Six Cargo invocations, each with zero tests**: compilation/harness evidence only, not native dialog or JNI correctness. |
| Migrated configuration and identity | **42 KMP/desktop POMs** matched the independent group/artifact/version/dependency mapping. Generated Cupertino resources retained the original namespace. These were unpublished generated metadata, not validated release packages. |

Earlier failed attempts remain in the ledger: restrictive baseline JDK provisioning,
offline dependency gaps, bounded disk termination, missing Cargo PATH/Wayland
development metadata and a TLS download failure. They are not silently replaced
by the later successful desktop run. The corrected harness does not downgrade the
declared Gradle 9.7.1 / Kotlin 2.4.20 / Compose 1.12.0 / AGP 9.4.0 toolchain.
It uses the official `platforms;android-37.0` package while retaining compileSdk37.
Separating the browser tests from production compilation and allowing 4 GiB/one
worker resolved the first run's Wasm production heap failure. Linux's three Gradle
phases completed in 5 minutes, 1 minute 13 seconds and 3 minutes 11 seconds. Some
compile/dependency work was cached; the 182 test executions were not.
Wasm webpack still reported four dynamic-dependency/bundle-size warnings; emitted
payloads included 534 KiB JavaScript, 5.71 MiB application Wasm and 8.24 MiB Skiko
Wasm. These are build outputs, not measured startup, memory, transfer or frame-time
performance, and the sample was not interactively certified.
The macOS framework linker warned that its bundle ID fell back to `Common` and
that four native compiler threads exceeded the runner's three processors. These
warnings remain documented qualifications, not hidden build failures. The
exact effective Xcode, Apple SDK and simulator runtime versions were not printed
in the captured command, so the passing run does not certify those version floors.
The corrected run therefore passed **300 target/host test executions in 42 XML reports**,
reusing **86 distinct original test functions**. The run's terminal success and
fresh task/XML evidence were inspected independently; Actions were subsequently
[disabled again](../testing/evidence/github-actions/actions-disabled-final-20261024.json).

Earlier direct compiler executions passed 15 unchanged IO/picker tests without
stubs. UI's 32 original common assertion bodies and three defect probes used
explicit framework adapters. Permission/geo, navigation, IO and native-feature
probes provide separate, clearly scoped confirmations; five million antipodal
trials found no NaN witness. **Do not sum overlapping test inventories, per-target
executions and adapter-based probes into a count of unique fully integrated
tests.** A passing characterization probe can mean that the reported bug was
reproduced, not fixed. `NO-SOURCE`, skipped and cached tasks are reported separately.

### Integrity and security checks

- Official Gradle wrapper JAR/distribution digests matched. Exact configured
  toolchain artifacts were checked as available, rather than assumed invalid or
  downgraded merely to obtain green output.
- Selected-host desktop runtime dependency export resolved **25 configurations**,
  **193 unique Maven coordinates**, **8,613 edges** and zero unresolved nodes.
  It covers the 24 included libraries and sample common, not the launcher's
  separately named `jvmRuntimeClasspath`, Android/Apple/browser/test/build graphs
  or embedded native binaries. See [scope and reproduction](../testing/runtime-dependencies.md).
- All 193 exact-coordinate OSV queries completed. The only match was the existing
  Low JavaFX-media 19 advisory **GHSA-47g3-mf24-6559 / CVE-2024-20925**; exploitability
  is unverified. The separate 202-coordinate Rust graph scan returned three
  informational unmaintained-crate notices, not demonstrated exploits. These
  registry observations are time-bounded and not a complete product SBOM.
- The recovered-history selected-marker scan enumerated **14,351 objects**,
  scanned **3,532 text blobs**, skipped 166 binary blobs, and found zero selected
  markers. This is not entropy analysis, compressed-attachment inspection,
  credential-validity testing or proof no secrets ever existed.
- **35 audit-tooling and 55 migration-tooling fixture tests passed**, with exit 0
  and no skips; these are not library runtime tests. [Final tooling receipt](../testing/evidence/final-tooling-verification.json).
  The seven additional migration fixtures ensure that a safe fresh clone needs no
  `upstream` remote, while an existing unguarded upstream still fails verification.
  This localized verifier correction does not change the library/toolchain/workflows
  tested in the successful CI run; the prior 48/52-test tooling receipts are retained.
- The [testing ledger](../testing/README.md) and [migration verification](../migration/verification.json)
  record tooling, documentation, checksum, offline bundle restore and read-only
  destination checks. A receipt names the SHA observed before it is committed;
  it cannot certify the later commit storing itself.
- A **fresh clone from the destination GitHub repository** at
  `c808c97fe555324ff92f75c3c55d0fc30114b7ea` passed all **551 integrity/control checks**,
  the audit validator, all 170 managed-issue checks, and the 35/55 tooling fixtures.
  It had only `origin`, no upstream remote or object alternates, and a clean working
  tree. [Preserved receipt/logs](../testing/evidence/fresh-clone-c808c97f/manifest.json).
  This independently verifies source/archive recovery without contacting Calf;
  it is not another Gradle/platform test run. The later commit storing these
  receipts is documentation/evidence-only, not a self-verifying commit.

No physical-device test, native-GUI automation, memory/thread sanitizer campaign,
CPU/memory/energy benchmark, release signing, distribution consumer certification
or binary-compatibility certification is implied. Broad target declarations and
successful builds are not proofs of native feature parity or release readiness.

## Preservation boundaries

The metadata archive preserves authors, timestamps, IDs, links, current bodies,
public edits, reviews and historical decisions as GitHub exposed them. It cannot
transplant GitHub authorship or recover unavailable/private/deleted content.
Wiki/projects/settings access failures, inconsistent star/fork counts, null edit
diffs, one 404 attachment and unarchived expired build artifacts are explicitly
documented. The source and Git/metadata copies are recoverable without Calf
remaining online; public dependency registries and platform SDKs are not vendored.

Offline bundle restoration verifies all **1,354 metadata-referenced commits** and
the complete **1,380-commit recovered graph**. This combines the original 1,009
advertised commits with additional historically referenced objects, including 371
supplemental archival refs; it does not rewrite or manufacture upstream history.
All 46 original branch names and 23 tags remain, with 68 non-main head/tag OIDs
unchanged and the original main an ancestor of additive migration commits.

The metadata archive contains **9,257 hashed files and 2,963 raw API responses**:
142 issues, 408 PRs, 448 conversation comments, 75 reviews, 13 inline comments,
3,028 timeline entries, 318 public edits, 23 releases, 306 deployment histories,
and 62 of 63 discovered attachments. Release JSON and historical PR refs are
archives, not newly published releases or impersonated live pull requests.
The [coverage record](../migration/metadata-coverage.md) is authoritative for
observation intervals, inaccessible endpoints and every known gap.

## Outstanding operational follow-up

The successful historical Pages deployment is **7300258890**, from preserved
`gh-pages` commit `2c3055c523ed6efe183d828b7a7942d357cd4d29` at
`2026-10-24T14:58:51Z`, actor `github-pages[bot]`. No migration command requested
it; the exact internal activation mechanism is unproven. Legacy branch publishing
is disabled by switching to workflow mode. Three REST deletion requests were
definitively rejected with HTTP422. Existing deployment unpublishing and public
URL/CDN state remain unverified; disabling Actions is not sufficient proof.

The owner has already been asked to use **Settings → Pages → Unpublish site**,
without deleting or changing the historical branch. [Issue #171](https://github.com/Apdelrahman1911/nativeCmpkit/issues/171)
and the [incident record](../migration/pages-incident.md) preserve this unresolved
work. No owner response, secret disclosure or successful cleanup is assumed.
This administrative task is independent of the completed source audit.

## Recommended next steps

1. Complete and verify the outstanding Pages unpublishing action without changing
   preserved history; keep Actions disabled outside supervised verification.
2. Establish a supported-platform preview boundary and fix data/memory/ownership
   High findings with narrowly scoped regression tests.
3. Repair permission orchestration, native modal/input/bar behavior and desktop
   distribution metadata. Preserve existing APIs or document compatible adapters.
4. Add real device/native consumer tests, dependency locks/verification, API/ABI
   gates, and artifact license/provenance checks.
5. Follow the full roadmap before feature expansion or major architectural change.
   Obtain separate explicit owner authorization before publishing anything.
