# First Preview Release readiness

**Status: NOT RELEASE-READY.** The owner authorized a first verified preview on
2026-10-24, not publication of unverified artifacts or silent acceptance of open
findings. `0.1.0-preview.1` is the **draft candidate version**, not a published
version, tag or availability promise. The baseline audit and its original
evidence remain intact. Current resolutions belong to this development phase.

**Current control mode: [contained publishing, authorized verification](containment.md).**
The owner's 2026-10-26 decision permits enabled Actions with all actions/reusable
workflows allowed and no mandatory SHA pinning. Routine development, CI testing,
dependency acquisition and consumer verification proceed autonomously, **without
subagents**. Packages/releases/deployments/Pages remain prohibited until the
applicable readiness and security gates pass. CI authority does not clear a gate.

The owner reaffirmed **contain without using subagents** on2026-10-27; the
verification authorization and all publication/security gates remain unchanged.

## Ordering and authority

1. Current upstream issue synchronization completed before production fixes;
   the [reconciliation and readback](upstream-sync-20261024T183300Z/README.md) retain
   original descriptions/labels/comments and duplicate dispositions.
2. Pages unpublishing was independently verified and #171 closed; see
   [the closure receipt](evidence/pages-unpublishing-closure.json). No release
   work authorizes restoring Pages or executing historical deployment workflows.
3. Fix and verify **all actionable** audit/imported/operational items. A new
   documentation file, source patch, passing defect-characterization probe or
   green compile is not issue closure.
4. Any future publication is lead-only and limited to **one first Preview
   Release**, only after every applicable gate has reviewed revision-bound
   evidence. The current CI authorization does not waive those requirements. Do not publish a
   partial-platform artifact set and label it complete.

## Gate ledger

[UIKit40449374922](native-ui-application-host.md#actual-delegate-initialization-failure-and-owning-repair)
passes actual Apple link/sign/install/owned cleanup, but crashes in its test-only
Objective-C initializer before any testcase/XML. The owning initializer/full-test
KLIB and bounded diagnostic repairs are compile/tooling evidence only; genuine
application, seven presenter/three host and complete matrix gates remain pending.

Latest additive evidence: [Android40449398030](checkpoint-android-runtime-20261027.md#actual-inline-dom-restoration-failure-and-real-url-fixture)
still fails24pass/1fail before navigator replacement; the genuine URL fixture
compiles, not executes. [Dependency005/006/008](dependency-lock-witness-20261027.md)
preserves both failed runtime suites/witnesses and supplies exact four-lock
rejection evidence, but no daemon binding, actual root/convention enforcement
or independent trust. No release gate/finding is promoted by these observations.

No row is automatically passed by checking in this plan. Each executed receipt
must include immutable source SHA, command, host/runtime/SDK, exit status, exact
nonzero test counts, input/output hashes and missing coverage.

| Gate | Required evidence | Present status / owner |
|---|---|---|
| Issue resolution | All 164 baseline findings plus current imported topics have verified dispositions; dependencies/risks reviewed, no automatic bulk closure | Pending; lead (historical area-owner handoffs retained) |
| Source/API baseline | Clean pre-development source, fresh compiled artifacts, original/public API inventory and reviewed before/after deltas | [Clean baseline completed](evidence/abi-baseline-94d2492e/README.md): 23 JARs, 331 inspected / 295 exported classes. [Dirty local comparison executed](evidence/jvm-diagnostic-20261024T224234Z-geo-repair/README.md): 23 JARs, 513 inspected / 449 exported; reviewed raw delta still exits1. Immutable release candidate/compiler ABI pending. |
| Library regressions | Actual common/JVM/browser/Android/Apple tests, no sample substitution; module bug-specific tests including boundary/concurrency/ownership | [Immutable development CI at6eb7c66](checkpoint-ci-20261026.md): core831 and macOS426 pass; iPhone332pass/16fail and WebView0 after compile failure; Windows421pass/1fail plus4 unexpected skips. Earlier JS004/Wasm004 and Android-device004 dirty diagnostics remain preserved. Later repairs, complete-platform and release-candidate results pending; host is not device. |
| Native behavior | Real JNI, native modal cancel/success/teardown, permission sequences, iOS security scopes/providers, AppKit/UIKit main-thread/native lifecycle checks | Real macOS Arm64 AppKit cancellation/diagnostic/borrowed-pointer tests passed at6eb7c66; only one host/scenario scope. UIKit application-host/native acceptance and Android device/minimum-API/provider gates remain pending; compilation cannot waive them. |
| Consumer matrix | Independently resolve/compile/run candidate artifacts on declared KMP targets and intended desktop slots/minimum runtimes | New [standalone consumer](../../tests/consumer/README.md), not yet compiled/executed |
| Published graph | All 21 roots × 7 coordinates (metadata, Android, desktop, JS, WasmJS, iOS Arm64/device and Arm64 simulator), complete redirect/dependency graph, exact version, no old Calf fallback | [Executed local-only metadata+desktop staging](checkpoint-ci-20261026.md#actual-maven-staging-attempt-remains-failed) exits1:38/42 coordinates,19/21 roots; picker/share correctly blocked by legal guards. Zero tests/strict consumers; remaining Android/browser/Apple graph pending. Earlier IO-only offline failures remain preserved; no pre-switch equivalence or registry publication claim. |
| Native payloads | Five intended desktop slots for each of picker/share; exact source/lock/toolchain/library-version/manifests, SHA/CPU, independently verified host loads | Pending; per-host partial checks explicitly remain partial |
| ABI and compatibility | Kotlin compiler dumps plus JVM descriptors/constants, JNI signatures/resource names and old consumer re-linking; reviewed intentional dependency changes | Two [local-JAR diagnostics](evidence/jvm-diagnostic-20261024T224234Z-geo-repair/README.md) passed the same 6 Java cases / 31 assertions; first exposed real EarthRadius access regression, second verified minimal repair using original bytecode and separate source compile. Raw 19→18 removals individually reviewed, comparator remains failed; staged/KMP ABI gates pending. |
| Legal distribution | Apache LICENSE/NOTICE + copied-code/font notices in actual artifacts/accompanying ZIPs; hash-verified native dependency license material and reviewed obligations | **Blocked**: [executed locked collection](evidence/native-license-material-20261024T193225Z/README.md) retains 16 archive-text gaps per native module; pinned JNI texts separately available for one, 15 objc2-family material gaps and SDK/license ambiguity remain. No live notice install/legal clearance. |
| Dependency trust | Exact locked Gradle/JS/Rust/Python graphs, artifact verification, resolved-graph vulnerability review; no floating release action/toolchain | Build-owner work; prior audit scan is not a scan of changed artifacts |
| Stable CI | Reviewed least-privilege workflows (exact action references optional); tests distinguished from compile/zero/cached/skipped results; bounded jobs; repeatable clean/checksum-proven outputs | Core/macOS pass at6eb7c66; Apple/Windows fail. New owned API35 device controller/APK configuration and source-byte fixes still need immutable hosted execution. No blanket green or release-gate pass. |
| Publication identity | Exact artifact list/version, registry permissions/ownership, signing requirements if applicable, package visibility, no unintended deployment | GitHub Packages proposed; Central/signing credentials not observed |
| Post-publication consumer | Download **published** bytes into an independent consumer, compare digests to verified candidate, resolve every variant, execute selected consumer smoke/regressions | Not started; no package has been published by this development phase |

The additive [2026-10-27 cache record](native-cache-security.md) preserves actual
Windows71 executions (66pass/5fail) and the subsequent immutable77/77 cache-suite
pass, with all five failed methods repaired, no removed cases and no unexpected
skips. Full-platform/loaded-DLL/native-owner requirements remain. The
[Android selection record](android-device-selection.md) preserves all three
zero-test hosted failures: run40430738675 atfa27c39f passes selector/report guards
and clean owned-emulator teardown but has no XML/testcases and an unknown
underlying UTP/device cause. Its early-diagnostics repair needs a fresh immutable
rerun. The [UIKit host investigation](native-ui-application-host.md) distinguishes
six actual generated Linux native fixture executions from zero library/iOS tests;
worker execution/failure propagation and genuine application hosting are pending.
Neither the812-method held preflight nor subsequent144-method synthetic CI checks
clear native, dependency, legal, ABI, consumer or stable-CI gates.

The additive [2026-10-27 repair checkpoint](checkpoint-verification-20261027.md)
retains the fourth failed Android run at569b1e16. Actual UTP XML filenames/hashes
exist in its public output while the declared intermediate/old collector is
empty: **zero parsed evidence does not prove zero native executions**. The
contents were not uploaded, so native counts and picker/WebView causes remain
unknown until a correctly collected immutable rerun. The source-held collector
regressions pass146 CI-tooling methods, not device tests. Actual Linux owned-worker
body/failure/termination diagnostics now pass their positive/negative contracts;
UIKit KLIB lowering succeeds separately. Neither proves Apple application hosting,
KGP JUnit integration, library-native behavior or any release/security gate.

[Held preflight005](evidence/ci-preflight-20261027-005/lead-review.json) separately
passes21 commands/826 Python-tooling methods, strict MkDocs and actionlint with
unchanged inputs. Counts reuse the146-method collector green; they are not
additional native/library/consumer executions or release verification.

The [subsequent actual Android review](checkpoint-android-runtime-20261027.md)
recounts67 executions (65pass/2fail) atab213b40. Picker fails at native hard-link
setup; WebView fails at its history precondition before replacement assertions.
The real-gesture repair and finite WebView-only rerun are not yet executed.
Neither root/SELinux bypass nor assumption skips are accepted. Actual Linux KGP
worker parsing now produces fresh positive/intentional-negative XML and correct
Gradle failure propagation despite protocol-controlled native result0; this is
four diagnostic executions, **zero library/iOS tests**. Genuine application
hosting and all native/dependency/legal/consumer/ABI gates remain open.

`verify_artifacts.py` always reports `release_readiness_certified=false`. Even
successful full static package inspection cannot certify behavior or legal
clearance. Its `complete_declared_artifact_matrix_requested` says what was asked
to be inspected, **not that the requested matrix passed**; inspect `success`,
failed checks and the linked runtime evidence separately.

The later [2026-10-26 tooling checkpoint](checkpoint-20261026.md) does not change
any gate: 737 offline Python methods passed, but strict documentation failed in
that full sweep. The separate link repair passes 73 development-tooling methods
and strict documentation with five generated-target checks; the two method
counts overlap. These are local tool/document checks, not new library, packaged
consumer, dependency-enforcement or hosted-CI results. Actions were disabled
at that checkpoint; the later owner decision authorizes verification CI.

## Credentials and destination assessment

Latest contained follow-up: [run40444608544](checkpoint-android-runtime-20261027.md#actual-real-gesture-run-and-inline-history-contract-repair)
executes25 WebView device tests (24pass/1fail before replacement); its inline-URL
fixture repair now compiles, not yet executes. The [genuine UIKit integration](native-ui-application-host.md#integrated-application-task-and-evidence-agreement-2026-10-27)
has actual full root UI main/test KLIB and model compilation plus synthetic
transport/receipt regressions. **Zero Apple/application/library-native methods**
execute in those Linux compiler/Python checks. Fresh immutable Android/iOS CI,
all remaining native/device/legal/dependency/consumer/ABI gates and verified
finding dispositions still govern publication. No gate or issue is cleared.

Read-only preparation inspected **names/presence only**: no GitHub repository
secrets, no secrets in the existing `github-pages` environment, no named local
Maven Central/signing environment variables, and no global Gradle property file
containing available publishing configuration were observed. No values were
printed or harvested. This is a scoped observation, not proof the owner has no
credentials anywhere.

Central publication/signing is therefore **not presently configured through
those channels**. A first Maven destination can instead be **GitHub Packages** at
`https://maven.pkg.github.com/Apdelrahman1911/nativeCmpkit`, using a separately
gated Actions job with `packages:write`, scoped to this repository and only the
verified candidate. A following GitHub prerelease can link the immutable package
coordinates, checksums, notices, changelog and verification receipts. Registry
access and package visibility must still be verified; authorization is not a
working credential/registry proof. Do not claim Maven Central availability.

GitHub Maven downloads generally require authentication even for public
packages. [Draft installation instructions](preview-installation.md) show a
read-only package token held outside source control; test that actual path after
publication. Never pass token values in command arguments/logs or commit Gradle
credentials. Token-scoped publication jobs must not run untrusted pull-request
code or inherited historical workflows.

## Producer-independent consumer design

The new `tests/consumer` build has its own settings/plugins/dependencies and
exclusive-content repository for the candidate group. It has **no project,
composite build, mavenLocal or producer source fallback**. All 21 identities are
explicit, including the permission aggregator and ten specialized permission
modules plus permission core. The three included unpublished prototypes/modules
(navigation, geo, maps) are not falsely promised as available Maven packages.

The initial fixture adds eight common executable contract methods, six desktop
filesystem/stream/concurrency methods and three packaged-JNI methods. These are
**test inventory, not passed counts**. The Composable probe compiles real public
APIs without pretending it exercised native presenters. JNI tests use real
artifact resources and isolated extraction/lookup paths; valid handle loops do
not certify GUI cancellation, invalid-pointer handling or memory sanitizers.
An additional Java fixture compiles against the old source-bound JARs and runs
unchanged class bytes on both old/new runtimes: six narrow cases / 31 assertions
passed [baseline-only fixture sanity](evidence/legacy-binary-baseline-sanity-20261024T195518Z/README.md),
then passed on both the first and repaired second **local-JAR** candidates with
identical baseline class hashes. That is six reused cases, not 12 independent
tests or a Maven consumer pass. A separate geo field probe failed the first
candidate and passed the repaired second with the original failed class bytes;
see [the complete paired evidence](evidence/jvm-diagnostic-20261024T224234Z-geo-repair/README.md).
**Zero of the 17 strict Maven Kotlin consumer methods have executed.** Python
fixtures only test the gate tools and synthetic inputs; their count is never a
Kotlin/Java/native behavior pass count.

All intended desktop slots remain: Linux glibc x64/Arm64, macOS x64/Arm64 and
Windows x64. Windows Arm64 had loader path strings but no working build/runtime
evidence in the original code; it is explicitly unsupported pending a tested
builder/runtime, not a removed known-working target. No musl/Intel-iOS/Node or
Kotlin/Native desktop support is newly claimed. Each intended slot still needs
its own evidence.

## ABI evidence provenance

The five preexisting audit JARs copied before source development are
**supplemental only**: their bytes and 180 javap-inspected classes were preserved
under `/tmp/nativecmpkit-abi-baseline`, with explicit provenance limitations.
They cannot alone close compatibility. A separate clean detached worktree at
`94d2492e` (the synchronization commit, before production fixes) **successfully
rebuilt all 21 published desktop JARs plus unpublished navigation/geo** with
bounded JDK17/Gradle9.7.1/Kotlin2.4.20/Rust1.98.0 inputs: 151 forced-rerun tasks,
exit 0, **zero tests**. The [completed receipt](evidence/abi-baseline-94d2492e/README.md)
binds fresh JAR hashes to 331 inspected classes / 295 exported class surfaces and
9,961 member records. It also proves equality of 369 selected production source
blobs to the original audit baseline, with build/identity/tests excluded.
Original build logic was retained; the formerly-unlocked generated Cargo graphs
are archived as observed offline resolutions, not retroactively called pinned
baseline inputs.

Two subsequent real local-JAR comparisons used held **dirty** input snapshots,
not an immutable release commit. The first 700 inputs / 23 JARs exposed a genuine
`LatLng.EarthRadius` Java-source/reflection regression despite the six-case
fixture's success. A minimal deprecated public-field repair and new regression
test changed exactly two source paths; the second 701 inputs / 23 JARs changed only
geo's JAR. The original baseline-compiled field fixture and separate Java-source
compilation then both passed, alongside 39 producer GEO desktop cases.

The raw JVM comparison remains **exit1, 18 removals / 311 additions** (first:19/311).
All remaining records have exact source-based classification: four synchronization
modifier-only records preserving invocation descriptors, four Kotlin-internal
removals, ten generated private/local implementation removals. No blanket
exclusion rewrote either failure. This is useful limited development feedback,
not universal Java/Kotlin compatibility or verified package consumption. Both
postchecks passed and their freezes were released; use preserved snapshots, not
later mutable output, to reproduce those results. **Maven/distribution/native/
release flags remain false.**

JVM `javap` public/protected signatures over-approximate Kotlin internals. A
changed declaration may need compatibility review even if descriptor linkage
still works; const values/default methods/constructors matter. Kotlin/Native,
Swift exports, Android platform-specific public types, nullability, inline bodies
and exact old Kotlin compiler compatibility need additional compiler/consumer
evidence. See [compatibility policy](compatibility.md).

## Prospective publication sequence after readiness and security gates pass

Verification Actions and local-only staging/consumer work are authorized now.
The publication steps below remain inert while gates are unsatisfied. Passing
local checks or enabling Actions does not authorize unverified distribution.

1. Freeze an additive commit and exact candidate version, with clean source and
   all baseline history/attribution preserved; no forced history/tag replacement.
2. Build every target/native slot once on its correct trusted host. Reuse only
   immutable successful input-bound outputs. Collect raw test reports and
   source/native/dependency/license provenance, then assemble the **same bytes**
   into an isolated candidate Maven repository.
3. Run static archive/metadata/license and full native/source matrix checks, then
   independent packaged consumers. Exercise minimum runtime/platform and native
   scenarios; reject source-compiled substitutes or missing reports.
4. Review every outstanding actionable issue, exact compatibility delta,
   changelog, license obligations and remaining limitations. No unverified
   platform is marked supported merely because its file exists.
5. Publish only the verified package set using the isolated, purpose-scoped job.
   Verify remote bytes and a fresh authenticated consumer. Reconcile partial
   registry failure before retrying; do not overwrite versions or pretend an
   incomplete set is successful.
6. Create the authorized GitHub **prerelease**, linking exact coordinates,
   verified installation and hash/notices/evidence receipts. Preserve failure
   observations as well as success. Keep unrelated publishing/Pages inert.

Until those steps have evidence, the correct state is an unpublished candidate,
not an announced first Preview Release.
