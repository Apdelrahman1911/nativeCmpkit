# nativeCmpkit development after the audit

The owner authorized fixes, library-level testing, efficient multi-platform CI and
the first **verified** preview on 2026-10-24. This is the live development record;
the [audit delivery report](../audit/final-report.md) remains a historical baseline.

## First actions

- [Pages resolution](evidence/pages-unpublishing/verification.json): owner action,
  authenticated null Pages status and public 404 responses verified; issue #171
  [closed with readback](evidence/pages-unpublishing-closure.json). Configuration
  and deployment history remain; Pages redeployment is not authorized.
- [Current upstream reconciliation](upstream-sync-20261024T183300Z/README.md):
  16 open issues, one separately recorded open PR; every issue already mapped.
  Fresh attributed descriptions, labels, comments and timelines are preserved.
  The apply receipt, not the existence of drafts, establishes posting/readback.

## Implementation and verification policy

Area owners maintain `resolutions/*.json` as JSON arrays, one record for each owned
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

## Working indexes

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
