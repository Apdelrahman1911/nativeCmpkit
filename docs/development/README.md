# nativeCmpkit development after the audit

The owner authorized fixes, library-level testing, efficient multi-platform CI and
the first **verified** preview on 2026-10-24. This is the live development record;
the [audit delivery report](../audit/final-report.md) remains a historical baseline.

Latest additive [consumer metadata/cache and actual UIKit delegate crash](checkpoint-consumer-metadata-alert-20261027.md):
UIKit40480810709 is a completed82-execution failure (81pass/1fail), not running;
the real plist repair is confirmed, then production wrongly changes UIKit's
Alert delegate. Popover-only ownership repair passes KLIB/model compilation,
not native execution;12 mandatory application methods now require fresh CI.
Consumer40486697786 actually stages all four coordinates/308 partial static
checks, then fails child DSL before any methods/XML. Repaired standalone help
configures successfully, not a packaged consumer. Metadata-aware exact staged/
loaded bindings, fresh uncached child Gradle homes and v2 declaration/runtime
cache keys now have124 source-held Python guards/actionlint. All seven consumer
methods/four classpaths and full21-root/native/security gates remain strict.
Ledger87implemented/69partial/8unresolved/0verified; no issue closure/publication.

Latest additive [consumer run/root-boundary repair](checkpoint-consumer-uikit-20261027.md#actual-partial-staging-failure-and-exact-root-build-repair):
40480857516 atc5e14c95 passes tooling, fails actual producer Gradle1/41.02s when
the init script looks up libraries inside included `convention-plugins`.737
immutable inputs and six independent copied files match; zero consumer methods/
XML. Exact canonical main-root binding repairs that boundary;48 Python guards
pass after three preserved failures, not repaired Gradle execution. Preflight016
passes23 commands/1078 Python methods/eight HTML anchors at15591 held inputs,
with both whitespace checks/strict docs/actionlint and unchanged heavy-build
reserve. New immutable consumer verification is required; UIKit40480810709 is
running at this observation. No finding/issue/release gate is promoted.

Latest contained follow-up: [real failed UIKit execution, owning manifest repair
and explicit partial packaged consumer](checkpoint-consumer-uikit-20261027.md).
UIKit40468870504 atb5a4508a executes82 (81pass/1fail),15 XML, zero skips; genuine
application Worker activation and cleanup succeed, but the first mandatory
native alert fails on the missing strict Compose plist Boolean and ten of11
application methods are absent. Manifest repair passes32 Python guards, not
Apple execution. New `consumer-core-io` CI independently stages/consumes four
Core/IO coordinates and requires seven named methods/exact loaded JAR bytes;
its adapter/Kotlin build remains unexecuted. Full21-root gates are unchanged.
Scoped201 Python methods/actionlint pass; older unchanged staging passes308
corrected static checks. All native/legal/dependency/consumer/ABI/release gates
remain; ledger87implemented/69partial/8unresolved/0verified. Both affected
profiles need new immutable execution after full source-held preflight.

Current contained follow-up: [actual Gradle ownership repair and exact native
identity after persistent UIKit startup failure](checkpoint-resource-native-20261027.md).
Five real controlled cleanup scenarios and380 dependency Python methods pass;
ordinary dependency trust and wrapper/other-host/descendant coverage remain open.
UIKit40460102044 retains simulator-migration and later startup-timeout failures,
both zero-test. Exact nonnull-pointer repair passes fresh full-test KLIB0/37.01s
and226 Python CI guards at712 held inputs, after a preserved compile failure.
Eleven genuine application methods are required; new immutable Apple runtime
verification is still needed. No issue closure, distribution or release gate.

Earlier contained follow-up: [reviewed Android pass, complete selected dependency
witness and reviewed UIKit startup failure/repair](checkpoint-verification-20261027-continuation.md).
Android40453976628 passes25/25 emulator executions (one native history method,
24 common methods), no skips. Six actual007 fixture invocations and12 external
client/daemon observations with6 bindings pass;148 observer methods pass and
core008 stays unchanged. UIKit's first attempt fails at runner Rust DNS before
testing; only that failed job is rerun at the same immutablebe32a7d6 revision.
Attempt2 links/signs/installs/cleans up, then crashes at synchronous root
attachment checking before any test/XML. The owning main-loop readiness fix
retains native assertions; five source guards and fresh full-test KLIB/model
compile pass, **not native execution**. See [the application record](native-ui-application-host.md#actual-activation-attachment-failure-and-bounded-startup-repair).
NATIVE-037 is partially-verified, not closed. Current ledger87implemented/
69partially-verified/8unresolved/0verified; no native/legal/dependency/consumer/ABI
or release gate is cleared. All prior failures and review corrections remain.

[Source-held preflight009](evidence/ci-preflight-20261027-009/lead-review.json)
passes21 commands/900 Python methods, strict MkDocs/actionlint and five actual
HTML anchors, before the later UIKit initializer/diagnostic edits. It executes
zero library/native/packaged consumers and does not circularly validate later
documentation, code or an immutable candidate.

## First actions

- [Pages resolution](evidence/pages-unpublishing/verification.json): owner action,
  authenticated null Pages status and public 404 responses verified; issue #171
  [closed with readback](evidence/pages-unpublishing-closure.json). Configuration
  and deployment history remain; Pages redeployment is not authorized.
- [Current upstream reconciliation](upstream-sync-20261024T183300Z/README.md):
  16 open issues, one separately recorded open PR; every issue already mapped.
  Fresh attributed descriptions, labels, comments and timelines are preserved.
  The apply receipt, not the existence of drafts, establishes posting/readback.
- [2026-10-27 read-only refresh](upstream-refresh-20261027T014340Z/README.md):
  all16 open issues still map to exactly one current destination context;
  zero imports/comments/closures needed. Full fresh timelines are archived;
  stable events match despite changed embedded repository/issue projections.
- [11:08 UTC fresh read-only refresh](upstream-refresh-20261027T110822Z/README.md):
  all16 contexts still match after full description/comment/timeline capture;
  no missing issues/imports/context edits/closures. Earlier archives unchanged.

## Implementation and verification policy

The single lead maintains `resolutions/*.json` as JSON arrays, one record for each
baseline finding. Each record has `id`, `status` (`implemented`, `partially-verified`,
`verified`, `unresolved`, or `not-applicable`), `changes`, `affected_paths`, `tests`, `remaining`
and `compatibility`. Test entries name commands, results and committed evidence;
unavailable tests are explicitly unavailable, not assumed successful.

`partially-verified` means the stated target/scenario actually passed but required
platform, immutable-revision, compatibility or native checks remain. `verified`
is reserved for lead-reviewed evidence satisfying the finding's required scope;
it does not mean the entire library is ready for release. Neither a new test nor
an isolated pass authorizes closing an issue automatically.

The lead reviews these against original `required_tests`, verifies the immutable
source revision, and decides issue closure. A passing characterization test might
prove the original bug exists, not that it is fixed. New test source without a run,
cached reports, platform stubs, `NO-SOURCE`, compilation and sample execution do
not count as native library functionality tests.

All 164 findings and imported topics remain in the roadmap until accurately
dispositioned. Feature requests for currently unimplemented modules must not be
silently declared fixed or expanded into unrelated features to inflate closure
counts. Public API and ownership changes need scoped design decisions and migration
guidance. Existing historical metadata and findings remain unchanged.

## Preview publication gate

Conditional owner authorization is not evidence that the gate passed. Before any
release/package publication, verify applicable issue fixes, runtime/native library
tests, stable cross-platform CI, packaged consumer fixtures, API compatibility,
native payload completeness/provenance, resolved dependency safety and artifact
licensing. Record exact versions, source SHA, task/test counts, hashes and limits.
No preview has been published by this phase at the time this document was started.

The **2026-10-26 owner decision** in [containment.md](containment.md) authorizes
automatic verification CI with Actions enabled, all actions/reusable workflows
allowed, and no mandatory SHA pinning. Routine development and dependency/consumer
verification need no additional approval. Work **without subagents**. Fixes and
immutable CI commits belong on `development/preview-hardening`; earlier local
receipts still describe dirty diagnostics, not a release candidate. Package/release
publication, deployments and Pages remain blocked behind the readiness/security
gates. See [ADR 0005](../decisions/0005-verification-actions-policy.md).

The owner reaffirmed **contain without using subagents** on **2026-10-27**.
Do not resume historical agents; continue autonomous bounded verification only.

## Working indexes

- [Metadata/cache containment and actual Alert crash](checkpoint-consumer-metadata-alert-20261027.md):
  reviewed immutable UIKit/consumer failures, separate source-held KLIB/DSL-only
  results, exact GMM cache-name/Maven-URL binding and uncached consumer ownership.
  Pending fresh12-case UIKit/seven-method consumer verification and all broad gates.
- [UIKit execution and partial Core/IO consumer](checkpoint-consumer-uikit-20261027.md):
  actual82-test application failure is distinct from32 plist and201 scoped
  Python passes; all seven independent consumer methods remain unexecuted.
  Preserve red evidence and strict full-matrix/native/security gates.
- [Actual Android runtime follow-up](checkpoint-android-runtime-20261027.md):
  immutable40436756084 executes67 (65pass/2fail) with three actual XML reports;
  both failures precede intended native assertions. Real-gesture WebView source
  and explicit one-module emulator profile need fresh execution. Hard-link
  provisioning remains fail closed, with no SELinux/root bypass. Actual Linux
  KGP parsing separately proves positive/intentional-negative worker outcomes;
  zero library/iOS methods or genuine UIKit hosting are implied.
- [2026-10-27 report-contract and cache-security checkpoint](checkpoint-20261027.md):
  Android's first owned-emulator attempt ran zero tests after an XML-path guard
  failure; actual AGP getters identify the repair. The Windows cache baseline
  executes71 (66pass/5fail), with no unexpected skips. [Owning cache repair](native-cache-security.md)
  has25 executed Linux source-level regressions and subsequently77/77 immutable
  Windows suite passes, with all five old failures passing and no removed cases.
  Android runtime results still need their own immutable review. No preview/issue closure
  is implied by tooling passes or new source.
- [Android device-selection contract](android-device-selection.md): the second
  immutable device attempt reaches all three tasks but executes zero tests after
  AGP's `UnsupportedOperationException`. Actual JDK17/Gradle/AGP method calls
  reproduce immutable serial-list mutation; the supported child-environment
  repair retains strict selector/report/teardown guards. The third immutable run
  [40430738675](evidence/github-actions/40430738675/lead-independent-review.json)
  passes those guards but still has zero XML/testcase evidence; its underlying
  UTP/device cause is unknown. The owning early-diagnostics collector needs a
  fresh immutable rerun, not a tooling-based native-success assumption.
- [2026-10-27 verification repair](checkpoint-verification-20261027.md): the
  fourth failed Android run exposes missed UTP XML, not proof of zero execution.
  Source-held collector regressions and actual Linux worker-body/failure probes
  are separate from still-pending device/UIKit/library verification.
- [Genuine UIKit application-host investigation](native-ui-application-host.md):
  Compose v2's Skiko scene is not an application host. An actual custom-entry
  Linux Kotlin/Native probe runs six repeated generated fixture executions/two
  methods, zero library/iOS tests; the subsequent owned-worker probe verifies
  body/failure/termination contracts on Linux only. Genuine simulator hosting
  and KGP parser integration remain unverified. Preserve failed probes too.
- [Three readback-verified progress comments atfa27c39f](evidence/issue-progress-fa27c39f/receipt.json):
  IO-022, NATIVE-031 and BUILD-007 retain original issue bodies/labels/states.
  Two installed-CLI `--slurp` read failures happened before posting; the portable
  pagination helper reconciled safely. No duplicate or issue closure is claimed.
- [Immutable hosted CI and contained failure follow-up](checkpoint-ci-20261026.md):
  core831 and macOS426 fresh passes; Apple/Windows failures independently reviewed
  and preserved. Android provider red/green, actual APK/configuration-only checks,
  incomplete legal-gated Maven staging and precise fixture/native limitations
  remain separate from release certification. No issue closed by this checkpoint.
- [2026-10-26 Actions policy transition](evidence/ci-policy-transition-20261026/observation.json):
  owner-enabled/all/no-required-pinning settings and read-only token defaults
  confirmed without a settings mutation. Current policy and executable guards
  now match that decision. [Local policy/CI preflight](evidence/ci-policy-verification-20261026-001/archive.json)
  passes all 20 bounded commands, **760 Python tooling methods**, strict MkDocs,
  history/migration/index checks and separate actionlint. These are **not hosted
  library runs**. The selected manual-dispatch matrix replaces sample builds with
  fresh library tests; packages/releases/deployments/Pages remain gated.
- [2026-10-26 contained verification checkpoint](checkpoint-20261026.md): all
  737 offline Python tests passed, but the original 20-command sweep failed at
  strict documentation validation. The owning link-generator/manual-link repair
  separately passes 73 development tests and strict MkDocs with five actual
  output-target checks. Both red runs and the earlier sweep failure are retained;
  counts overlap and are not library/native/consumer or hosted-CI evidence.
  That checkpoint's then-current read-only observation found Actions disabled;
  the later [owner-authorized transition](evidence/ci-policy-transition-20261026/observation.json)
  instead confirms enabled/all/no-required-pinning. The earlier observation found
  Pages status null, no GitHub releases, #171 closed and `main` unchanged.
- [2026-10-25 contained checkpoint](checkpoint-20261025.md): full JS004 and Wasm004
  pass290/290 each across19 requested modules; focused IO/NAV desktop73/73 and
  IO Android-host21/21 pass. The latter is JVM/Robolectric, **not device testing**.
  Android-device004 remains failed/incomplete (IO16/17, no picker XML). Earlier
  Wasm/compiler/tooling failures are preserved. These are dirty-worktree
  diagnostics, not immutable release-candidate or hosted-CI results.
- [Finding status and dependency-ordered roadmap](status.md), with the original
  530 acceptance requirements preserved in [the machine-readable index](status.json).
  This is an owner-ledger index, not runtime certification or an issue-closure list.
- [Release gates](release-readiness.md) and [compatibility contract](compatibility.md).
- Area implementation records: [build/dependencies](BUILD.md), [IO/pickers](IO.md),
  [native camera/share/WebView](NATIVE.md), [permissions](PERM.md), [geolocation](GEO.md),
  [navigation/icons](NAV.md), [UI controls](UI-controls.md), and [UIKit](UI-native.md).
- [Android library device tests](IO-android-device-tests.md): preserve each failed
  attempt and distinguish native test-harness limitations from demonstrated
  production defects. The [fourth device run](evidence/android-device-004/archive.json)
  passed16 IO cases and failed its metadata precondition; picker emitted no XML
  before timeout. Its691 selected input hashes were unchanged. The earlier
  [third run](evidence/gradle/third-android-device.summary.json), in which all three
  selected suites failed, remains archived; neither run is a release candidate.

After area-ledger changes, regenerate and independently check the index:

```sh
python3 scripts/development/validate_resolutions.py --write
python3 scripts/development/validate_resolutions.py --check
```

The validator checks complete IDs, mappings, dependencies and schema. It does
not certify linked test evidence, promote statuses, or close GitHub issues.

GitHub Packages can use a purpose-scoped Actions token and authenticated Maven
consumer configuration; unavailable Central credentials must not be represented
as a successful Central publication. Publication workflow templates stay outside
active workflows until all required gates pass. Documentation hosting stays off.
